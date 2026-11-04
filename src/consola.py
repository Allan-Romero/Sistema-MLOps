"""Salida de consola en UTF-8 para los puntos de entrada del proyecto.

En Windows la consola usa cp1252 y no puede codificar los caracteres que
imprimen algunas dependencias: MLflow escribe un emoji al cerrar cada
ejecución, lo que interrumpía el pipeline después de registrar la versión
en MLflow y antes de persistirla en PostgreSQL.
"""

import sys


def usar_utf8():
    """Reconfigura la salida estándar y la de error para escribir en UTF-8."""
    for flujo in (sys.stdout, sys.stderr):
        reconfigurar = getattr(flujo, "reconfigure", None)
        if reconfigurar is None:
            continue
        try:
            reconfigurar(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            # Una salida ya redirigida o cerrada no admite reconfiguración;
            # no es motivo para interrumpir la ejecución.
            pass
