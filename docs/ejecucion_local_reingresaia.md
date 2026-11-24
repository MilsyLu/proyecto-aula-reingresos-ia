# ReingresaIA en su computador — React + FastAPI

Esta guía corresponde a la rama `experiment/reingresaia-ui`, que fue
actualizada desde `main` el 24 de noviembre de 2026. Los cambios de
tipografía se realizan **solo en esta rama**.

## Requisitos

- **Git**
- **Python 3.12** y `pip`
- **Node.js 22 LTS** y `npm`
- Internet para instalar dependencias por primera vez
- Aproximadamente 2 GB disponibles para dependencias, modelos y compilación

Compruebe las versiones:

```bash
git --version
python --version
node --version
npm --version
```

### 1. Descargar y seleccionar la rama

En una terminal, en la carpeta donde guarde sus proyectos:

```bash
git clone https://github.com/MilsyLu/proyecto-aula-reingresos-ia.git
cd proyecto-aula-reingresos-ia
git fetch origin
git switch experiment/reingresaia-ui
git pull --ff-only origin experiment/reingresaia-ui
```

Si ya tiene clonado el repositorio, abra esa carpeta y ejecute únicamente
los tres últimos comandos.

### 2. Windows 10/11 (PowerShell)

Desde **la raíz del repositorio**:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-api.txt
```

Abra **dos terminales** en esa misma carpeta.

**Terminal 1 — API FastAPI:**

```powershell
.\.venv\Scripts\python.exe -m uvicorn api.principal:app --reload --host 127.0.0.1 --port 8001
```

**Terminal 2 — React:**

```powershell
cd web
npm ci
npm run dev
```

Abra **http://localhost:5173** en el navegador.

La API se consulta en **http://127.0.0.1:8001/api/salud**.
La documentación de la API está en
**http://127.0.0.1:8001/api/documentacion**.

No es necesario iniciar Streamlit para esta versión web.

### 3. CachyOS, Arch o Linux

Desde la raíz del repositorio:

```bash
python3.12 -m venv .venv
./.venv/bin/python -m pip install -r requirements-api.txt
```

En una primera terminal:

```bash
./.venv/bin/python -m uvicorn api.principal:app --reload --host 127.0.0.1 --port 8001
```

En otra terminal, desde la raíz del proyecto:

```bash
cd web
npm ci
npm run dev
```

Abra **http://localhost:5173**.

Si Linux no tiene `python3.12`, instale Python 3.12 o use un gestor como
`pyenv`; no cambie arbitrariamente la versión de scikit-learn porque se
carga un modelo entrenado y serializado en una versión concreta.

### 4. Verificar

**La API:**

- Abra `http://127.0.0.1:8001/api/salud`.
- Debe responder un JSON con `estado: "en pie"`.
- `front: false` es normal mientras React se ejecuta por separado con Vite.

**La página web:**

- Abra `http://localhost:5173`.
- Inicie sesión con una de las cuentas demostrativas mostradas en la página.
- Pruebe menú lateral, tablas, formulario individual, tema claro y oscuro.
- En pantallas estrechas, compruebe que las tablas se puedan desplazar sin
  ocultar opciones ni cortar etiquetas importantes.

**Comprobar compilación (terminal 2):**

```bash
npm run build
npm run lint
```

**Comprobar las pruebas del servidor (raíz del repositorio):**

```bash
# En Windows, use .\.venv\Scripts\python.exe en lugar de python.
python -m unittest discover -s tests -v
```

Las pruebas requieren las dependencias correspondientes. El comando anterior
puede necesitar el entorno completo (`requirements.txt`, que incluye
Streamlit y paquetes de desarrollo) para pruebas históricas relacionadas
con ese programa; las dependencias de la aplicación React/FastAPI se
instalan desde `requirements-api.txt`.

### 5. Problemas comunes

- **La web abre pero indica error de red:** compruebe que la API se ejecuta
  en el puerto **8001**. El proxy de `web/vite.config.ts` usa ese puerto.
- **El puerto 8001 está ocupado:** cambie la API a `--port 8002` y
  configure `PUERTO_API=8002` antes de `npm run dev`.
  En PowerShell: `$env:PUERTO_API="8002"`.
- **El puerto 5173 está ocupado:** Vite puede abrir otro puerto; utilice la
  URL que muestre la terminal.
- **No se encuentra `uvicorn`:** ejecute el comando con el Python
  del entorno virtual, no con otro Python del sistema.
- **Faltan módulos Python:** verifique la instalación con
  `python -m pip install -r requirements-api.txt` dentro del entorno.
- **`npm` no existe:** instale Node.js 22 y reinicie la terminal.
- **Los cambios de letra no se ven:** verifique la rama con
  `git branch --show-current`; reinicie `npm run dev` o recargue la página.

## Qué cambia respecto a Streamlit

La versión nueva tiene un frontend `web/` React/TypeScript y un backend
`api/` FastAPI. El servidor calcula las probabilidades con el mismo
modelo oficial `models/gradient_boosting_ajustado.joblib`, y el frontend
solicita los resultados por HTTP. En desarrollo los dos procesos se
inician por separado y Vite redirige `/api` al servidor Python.

**Privacidad:** para esta demostración utilice exclusivamente datos
ficticios o anonimizados. Los registros de seguimiento se guardan
localmente en SQLite por el backend.

## Ajustes tipográficos de la rama experimental

El CSS de `web/src/estilos.css` elevó la fuente base del aplicativo de
13 a 16 px y aumentó 108 declaraciones tipográficas pequeñas de controles,
navegación, etiquetas y textos secundarios. El menú lateral se amplió
de 252 a 280 px y se reforzó el tamaño de las tablas.

Se conserva la identidad visual (paleta morada/teal, componentes, tipografías
DM Sans y Nunito Sans) y el diseño responsive. Verifique el resultado en su
navegador: este cambio no ha sido validado visualmente en todos los tamaños.
