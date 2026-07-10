# Definition of Done (DoD) — Plataforma MLOps

**Proyecto:** Desarrollo de una Plataforma MLOps Automatizada con Pipeline CI/CD
**Equipo:** Joseph Reyes · Allan Romero
**Tarea:** S0-T8 — Definir Definition of Done

---

## ¿Qué es el Definition of Done?

El Definition of Done es el conjunto de condiciones que **toda tarea** del proyecto debe cumplir antes de considerarse finalizada y moverse a la columna "Done" del tablero. Es un estándar único y transversal: aplica por igual a cualquier tarea, sin importar si es de desarrollo, base de datos, dashboard o documentación.

Este documento es distinto de los criterios de aceptación de cada incidencia. Los criterios de aceptación son específicos de cada tarea; el Definition of Done es general y se cumple **además** de ellos.

> Una tarea está terminada cuando cumple sus criterios de aceptación **y** todos los puntos de este Definition of Done.

---

## Checklist obligatorio

Toda tarea debe cumplir como mínimo:

### 1. Código funcional
El código se ejecuta localmente sin errores y hace lo que la tarea pide. No se acepta código que "casi funciona" o que está a medias.

### 2. Código probado
Se verificó que la funcionalidad opera correctamente, ya sea ejecutándola manualmente o mediante pruebas automatizadas. Se probó al menos un caso real de uso.

### 3. Código subido al repositorio
El trabajo está en GitHub, en la rama correspondiente (nunca directo a `main`). No se considera terminado nada que solo exista en el computador de un integrante.

### 4. Commit descriptivo
Los commits siguen la convención acordada y describen claramente qué se hizo (por ejemplo: `feat: agregar endpoint /predict en FastAPI`). No se aceptan mensajes vagos como "cambios" o "arreglos".

### 5. Evidencia adjunta
La tarea incluye una prueba de que se completó: captura de pantalla, salida de un comando ejecutado, o resultado de una prueba. Esta evidencia se guarda para el documento final de la tesis.

### 6. Revisado por el otro integrante
El otro compañero revisó el trabajo mediante un Pull Request, verificando que funciona, que el código es entendible y que cumple los criterios de aceptación. Una tarea no se cierra con la sola opinión de quien la hizo.

### 7. Sin conflictos de integración
La rama se fusiona a `develop` sin conflictos de Git. Si hay conflictos, se resuelven antes de dar por terminada la tarea.

### 8. Documentación actualizada cuando aplique
Si la tarea cambia la forma de instalar, ejecutar o usar algo, se actualiza el README o la documentación correspondiente. Aplica solo cuando el cambio lo amerita.

---

## Regla de uso

Antes de mover una tarea a la columna "Done", el integrante responsable revisa esta lista punto por punto. Si algún punto no se cumple (y aplica a la tarea), la tarea regresa a "In Progress" hasta corregirse.
