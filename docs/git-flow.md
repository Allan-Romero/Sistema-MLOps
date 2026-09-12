# Flujo de Trabajo con Git — Plataforma MLOps

**Proyecto:** Desarrollo de una Plataforma MLOps Automatizada con Pipeline CI/CD
**Equipo:** Joseph Reyes · Allan Romero
**Tarea:** S0-T5 — Definir ramas de trabajo

---

## 1. Estrategia de ramas

El equipo trabaja con una versión simplificada de Git Flow, adecuada para un equipo de dos personas. Se usan tres tipos de ramas:

| Rama | Rol | ¿Se programa aquí? |
|------|-----|--------------------|
| `main` | Rama estable. Solo contiene versiones probadas, revisadas y funcionales. Es la versión oficial del proyecto. | No |
| `develop` | Rama de integración. Aquí se fusionan y prueban en conjunto los avances de ambos integrantes. | No (solo se integra) |
| `feature/*` | Ramas temporales de desarrollo. Una por cada funcionalidad. Se trabaja de forma aislada. | Sí |

**Regla de oro:** el código fluye siempre en una sola dirección.

```
feature/* → develop → main
```

Nunca se programa directamente sobre `main` ni sobre `develop`, y nunca se fusiona de `main` hacia una feature.

---

## 2. Ramas feature por integrante

| Integrante | Ramas feature |
|------------|---------------|
| Joseph | `feature/model-api`, `feature/pipeline-mlflow`, `feature/rollback` |
| Allan | `feature/db-dashboard`, `feature/drift-monitoring`, `feature/results-doc` |

Las ramas feature se crean **a partir de `develop`** y se eliminan una vez fusionadas.

---

## 3. Convención de nombres

- **Ramas feature:** `feature/nombre-corto-en-minusculas` (usar guiones, no espacios).
  - Ejemplos: `feature/model-api`, `feature/drift-monitoring`
- **Ramas de corrección puntual (opcional):** `fix/descripcion-corta`
- Nada de nombres genéricos como `feature/prueba` o `feature/cambios`.

---

## 4. Convención de commits

Formato recomendado (Conventional Commits):

```
<tipo>: <descripción breve en presente>
```

Tipos permitidos:

- `feat:` nueva funcionalidad
- `fix:` corrección de un error
- `docs:` cambios en documentación
- `refactor:` reorganización de código sin cambiar comportamiento
- `test:` agregar o ajustar pruebas
- `chore:` tareas de configuración o mantenimiento

Ejemplos:

```
feat: agregar endpoint /predict en FastAPI
fix: corregir error de conexión a PostgreSQL
docs: actualizar README con instrucciones de despliegue
```

---

## 5. Flujo de trabajo diario

1. Ubicarse en `develop` y actualizar:
   ```bash
   git checkout develop
   git pull origin develop
   ```
2. Crear (o cambiarse a) la rama feature correspondiente:
   ```bash
   git checkout -b feature/mi-funcionalidad
   ```
3. Trabajar, hacer commits pequeños y descriptivos.
4. Subir la rama al remoto:
   ```bash
   git push -u origin feature/mi-funcionalidad
   ```
5. Abrir un **Pull Request** de `feature/*` hacia `develop`.
6. El otro integrante revisa (código + funcionamiento + criterios de aceptación).
7. Si todo está bien, se aprueba y se fusiona a `develop`.
8. Al cerrar cada sprint, `develop` se fusiona a `main`.

---

## 6. Reglas del equipo

- No se sube nada directo a `main`.
- Toda fusión a `develop` y a `main` pasa por Pull Request.
- Cada Pull Request debe incluir: descripción, evidencia (captura o comando ejecutado) y checklist de criterios de aceptación.
- Una rama feature no se fusiona hasta pasar el Review & Testing.
- Las ramas feature se eliminan después de fusionarse.

---

## 7. Comandos de configuración inicial (ejecutados una vez)

```bash
# Crear develop a partir de main
git checkout main
git pull origin main
git checkout -b develop
git push -u origin develop

# Crear una rama feature de ejemplo
git checkout develop
git checkout -b feature/db-dashboard
git push -u origin feature/db-dashboard
```
