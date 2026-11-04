"""Renderiza Streamlit con consultas reales sobre la base efímera del E2E."""
import json
from streamlit.testing.v1 import AppTest
from src.database.crud import obtener_version_activa


def main():
    evidencia = []
    for caso in ("churn", "fraude"):
        app = AppTest.from_file("dashboard/app.py", default_timeout=120).run()
        app.selectbox[0].set_value(caso).run()
        assert not app.exception, [str(e) for e in app.exception]
        activa = obtener_version_activa(caso)[0][2]
        indicadores = {m.label: m.value for m in app.metric}
        assert indicadores["Versión en producción"] == activa, indicadores
        assert int(indicadores["Rollbacks"]) >= 1, indicadores
        assert int(indicadores["Promociones"]) >= 2, indicadores
        mensajes = [elemento.value for elemento in app.info]
        assert any("Versión ganadora: " + activa in mensaje for mensaje in mensajes), mensajes
        evidencia.append({"caso_uso": caso, "indicadores": indicadores, "mensajes": mensajes})
    print(json.dumps(evidencia, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
