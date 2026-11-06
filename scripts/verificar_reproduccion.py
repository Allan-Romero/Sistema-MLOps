"""Comprueba manifiestos, versiones instaladas y, opcionalmente, servicios.

No lee .env ni imprime credenciales. No crea bases, entrena ni modifica modelos.
Uso: python scripts/verificar_reproduccion.py --solo-manifiestos
     python scripts/verificar_reproduccion.py --servicios
"""
import argparse
from datetime import datetime, timezone
from importlib import metadata
import json
from pathlib import Path
import platform
import re
import sys
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]


def normalizar(nombre):
    return re.sub(r"[-_.]+", "-", nombre.lower())


def verificar_manifiestos():
    constraints = ROOT / "requirements/constraints.txt"
    versiones = {}
    for linea in constraints.read_text(encoding="utf-8-sig").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        nombre, version = linea.split("==", 1)
        nombre = normalizar(nombre)
        if nombre in versiones:
            raise ValueError(f"Versión duplicada en constraints: {nombre}")
        versiones[nombre] = version
    visitados = set()
    requeridos = set()
    def visitar(ruta):
        ruta = ruta.resolve()
        if ruta in visitados:
            return
        visitados.add(ruta)
        for linea in ruta.read_text(encoding="utf-8-sig").splitlines():
            linea = linea.strip()
            if not linea or linea.startswith("#"):
                continue
            if linea.startswith(("-r ", "-c ")):
                destino = (ruta.parent / linea[3:]).resolve()
                if not destino.is_file():
                    raise FileNotFoundError(destino)
                if linea.startswith("-r "):
                    visitar(destino)
                elif destino != constraints.resolve():
                    raise ValueError(f"Fuente de versiones no centralizada: {destino}")
            else:
                if re.search(r"[=<>;]", linea):
                    raise ValueError(f"Restricción fuera de constraints: {ruta.name}: {linea}")
                nombre = normalizar(linea.split("[", 1)[0])
                if nombre not in versiones:
                    raise ValueError(f"Dependencia sin versión central: {nombre}")
                requeridos.add(nombre)
    visitar(ROOT / "requirements.txt")
    return {nombre: versiones[nombre] for nombre in sorted(requeridos)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--solo-manifiestos", action="store_true")
    parser.add_argument("--servicios", action="store_true")
    args = parser.parse_args()
    requeridos = verificar_manifiestos()
    resultado = {"fecha_utc": datetime.now(timezone.utc).isoformat(),
                 "python": platform.python_version(), "plataforma": platform.system(),
                 "manifiestos": "correctos", "dependencias_directas": requeridos}
    errores = []
    if not args.solo_manifiestos:
        instaladas = {}
        for nombre, esperada in requeridos.items():
            try:
                actual = metadata.version(nombre)
            except metadata.PackageNotFoundError:
                actual = None
            instaladas[nombre] = actual
            if actual != esperada:
                errores.append(f"{nombre}: esperado {esperada}, instalado {actual}")
        resultado["versiones_instaladas"] = instaladas
    if args.servicios:
        servicios = {}
        for nombre, url in {"api": "http://localhost:8000/health",
                            "dashboard": "http://localhost:8501/_stcore/health",
                            "mlflow": "http://localhost:5000/health"}.items():
            try:
                with urlopen(url, timeout=10) as respuesta:
                    servicios[nombre] = respuesta.status
            except Exception as error:
                servicios[nombre] = type(error).__name__
                errores.append(f"No responde {nombre}")
        resultado["servicios_http"] = servicios
    resultado["errores"] = errores
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
