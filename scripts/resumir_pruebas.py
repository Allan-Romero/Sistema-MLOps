"""Resume JUnit, cobertura y omisiones sin confundirlos con evidencia E2E.

Uso: python scripts/resumir_pruebas.py --salida docs/evidencias/sprint5/pruebas_resumen.json
No ejecuta pruebas ni modifica sus resultados. Falla si faltan reportes.
"""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
CRITICOS = (
    "src/database/model_promotion.py", "src/training/promotion_policy.py",
    "src/api/ab_routing.py", "src/api/ab_models.py",
    "src/monitoring/rollback_policy.py", "src/monitoring/rollback_service.py",
    "src/monitoring/rollback_auto.py", "src/monitoring/experiment_service.py",
)


def auditar_omisiones():
    marcas = []
    for ruta in sorted((ROOT / "tests").rglob("*.py")):
        for nodo in ast.walk(ast.parse(ruta.read_text(encoding="utf-8-sig"))):
            nombre = ""
            if isinstance(nodo, ast.Attribute):
                nombre = nodo.attr
            elif isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name):
                nombre = nodo.func.id
            if nombre in {"skip", "skipif", "xfail", "importorskip"}:
                marcas.append({"archivo": ruta.relative_to(ROOT).as_posix(),
                               "linea": nodo.lineno, "marca": nombre})
    return marcas


def version(distribucion):
    try:
        return importlib.metadata.version(distribucion)
    except importlib.metadata.PackageNotFoundError:
        return "no instalada"


def resumen(junit, cobertura):
    raiz = ET.parse(junit).getroot()
    casos = raiz.findall(".//testcase")
    omitidos = [{"clase": c.get("classname"), "prueba": c.get("name"),
                 "motivo": c.find("skipped").get("message", "")}
                for c in casos if c.find("skipped") is not None]
    fallos = sum(c.find("failure") is not None for c in casos)
    errores = sum(c.find("error") is not None for c in casos)
    datos = json.loads(cobertura.read_text(encoding="utf-8"))
    total = datos["totals"]
    firmas = {}
    for carpeta in ("src", "tests", "scripts"):
        for ruta in sorted((ROOT / carpeta).rglob("*.py")):
            firmas[ruta.relative_to(ROOT).as_posix()] = hashlib.sha256(ruta.read_bytes()).hexdigest()
    archivos = {ruta.replace("\\", "/"): valor for ruta, valor in datos["files"].items()}
    criticos = {ruta: archivos[ruta]["summary"] for ruta in CRITICOS if ruta in archivos}
    return {
        "generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "base_git": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "nota_version": "Los hashes identifican archivos del árbol de trabajo probado, incluidos cambios todavía no confirmados.",
        "entorno": {"python": platform.python_version(), "sistema": platform.system(),
                    "pytest": version("pytest"), "pytest_cov": version("pytest-cov"),
                    "coverage": version("coverage"), "scikit_learn": version("scikit-learn")},
        "suite": {"casos": len(casos), "aprobados": len(casos) - len(omitidos) - fallos - errores,
                  "fallos": fallos, "errores": errores, "omitidos": len(omitidos)},
        "omisiones_ejecucion": omitidos,
        "marcas_omision_en_codigo": auditar_omisiones(),
        "cobertura_total": total,
        "cobertura_componentes_criticos": criticos,
        "alcance": "Pruebas locales unitarias y HTTP en proceso; las conexiones SQL son dobles en esta suite. El job delivery prueba contenedores y PostgreSQL reales por separado.",
        "hashes_archivos_python": firmas,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--junit", type=Path, default=ROOT / "reports/sprint5/junit.xml")
    parser.add_argument("--cobertura", type=Path, default=ROOT / "reports/sprint5/coverage.json")
    parser.add_argument("--salida", type=Path)
    argumentos = parser.parse_args()
    texto = json.dumps(resumen(argumentos.junit, argumentos.cobertura), ensure_ascii=False, indent=2)
    if argumentos.salida:
        argumentos.salida.parent.mkdir(parents=True, exist_ok=True)
        argumentos.salida.write_text(texto + "\n", encoding="utf-8")
    else:
        print(texto)


if __name__ == "__main__":
    main()
