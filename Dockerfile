# ReingresaIA — imagen de la aplicación completa.
#
# Un solo contenedor sirve las dos cosas: las rutas de la API y el build de
# React. Por eso no hay CORS que configurar ni dos despliegues que mantener
# sincronizados, y la aplicación vive en un solo enlace.
#
# Pensada para Hugging Face Spaces, que espera el puerto 7860.
#
#   docker build -t reingresaia .
#   docker run -p 7860:7860 reingresaia

# --- 1. Se construye el front -----------------------------------------------
FROM node:22-slim AS front

WORKDIR /build

# Primero solo los manifiestos: si no cambian, Docker reutiliza la capa de
# node_modules y la construcción tarda segundos en vez de minutos.
COPY web/package.json web/package-lock.json ./
RUN npm ci

COPY web/ ./
RUN npm run build


# --- 2. Se sirve todo desde Python ------------------------------------------
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements-api.txt ./
RUN pip install --no-cache-dir -r requirements-api.txt

# Solo lo que el servidor necesita para funcionar. Quedan fuera los cuadernos,
# los datos crudos y las figuras: pesan y no se usan en producción.
COPY api/ ./api/
COPY app/ ./app/
COPY src/ ./src/
COPY models/ ./models/
COPY reports/ ./reports/
COPY --from=front /build/dist ./web/dist

# Hugging Face corre el contenedor con un usuario sin privilegios.
# La carpeta donde vive la base de datos del seguimiento. Se crea ANTES de
# cambiar de usuario, y por eso el chown de abajo la alcanza.
#
# Ojo con esto: un volumen con nombre recien creado hereda el dueno de la
# carpeta que encuentra en la imagen. Si /app/datos no existiera aqui, el
# volumen quedaria de root y el contenedor no podria escribir la base. Falla
# en silencio, al primer paciente que alguien registre.
RUN mkdir -p /app/datos

RUN useradd --create-home --uid 1000 usuario && chown -R usuario:usuario /app
USER usuario

EXPOSE 7860

# Un solo worker a propósito. El servidor gratis tiene dos núcleos compartidos y
# el entrenamiento en vivo ya se come uno; varios workers se estorbarían entre
# sí y además cada uno cargaría su propia copia del modelo en memoria.
CMD ["uvicorn", "api.principal:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
