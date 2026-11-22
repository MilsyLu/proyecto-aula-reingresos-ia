# -*- coding: utf-8 -*-
"""ReingresaIA — API y servidor de la aplicación.

Un solo proceso sirve dos cosas: las rutas bajo `/api` y, en producción, el
build de React que queda en `web/dist`. Por eso no hay CORS que configurar ni
dos despliegues que mantener sincronizados.

Arrancar en desarrollo:
    uvicorn api.principal:app --reload --port 8000

El front se levanta aparte con `npm run dev` y su proxy manda `/api` aquí.
"""
from __future__ import annotations

import os
import secrets
import sys
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.middleware.sessions import SessionMiddleware

BASE = Path(__file__).resolve().parent.parent
for ruta in (str(BASE), str(BASE / "src"), str(BASE / "app")):
    if ruta not in sys.path:
        sys.path.insert(0, ruta)

from api import autenticacion as auth  # noqa: E402
from api import prediccion  # noqa: E402

DIST = BASE / "web" / "dist"

app = FastAPI(
    title="ReingresaIA",
    description="Predicción de reingreso hospitalario a 30 días. Prototipo académico.",
    version="1.0.0",
    docs_url="/api/documentacion",
    openapi_url="/api/openapi.json",
)

# La clave firma la cookie de sesión. En el servidor se pone como secreto; si
# falta, se genera una al arrancar, y entonces las sesiones no sobreviven a un
# reinicio. Para un prototipo es aceptable, pero conviene saberlo.
CLAVE = os.environ.get("REINGRESAIA_CLAVE_SESION")
if not CLAVE:
    CLAVE = secrets.token_urlsafe(32)
    print(
        "AVISO: no hay REINGRESAIA_CLAVE_SESION. Se generó una clave temporal: "
        "las sesiones se cierran cada vez que el servidor reinicia.",
        file=sys.stderr,
    )

app.add_middleware(
    SessionMiddleware,
    secret_key=CLAVE,
    session_cookie="reingresaia",
    same_site="lax",
    https_only=os.environ.get("REINGRESAIA_HTTPS", "").lower() == "si",
    max_age=8 * 60 * 60,  # una jornada
)


# ===========================================================================
# Sesión
# ===========================================================================

class Credenciales(BaseModel):
    usuario: str = Field(min_length=1, max_length=64)
    contrasena: str = Field(min_length=1, max_length=256)


@app.post("/api/entrar")
def entrar(credenciales: Credenciales, peticion: Request):
    datos = auth.verificar(credenciales.usuario, credenciales.contrasena)
    if not datos:
        # Un solo mensaje para usuario inexistente y contraseña incorrecta: decir
        # cuál de los dos falló le regala información a quien esté probando.
        return JSONResponse({"detail": "Usuario o contraseña incorrectos."}, status_code=401)
    peticion.session["sesion"] = datos
    return datos


@app.post("/api/salir")
def salir(peticion: Request):
    peticion.session.clear()
    return {"salio": True}


@app.get("/api/sesion")
def sesion(peticion: Request):
    """Quién está dentro, o nadie.

    Responde 200 aunque no haya sesión. Preguntar si hay sesión abierta es una
    pregunta legítima, y "no hay" es una respuesta válida, no un error: devolver
    401 aquí llenaba la consola del navegador de fallos rojos cada vez que
    alguien abría la portada sin haber entrado.
    """
    return {"sesion": auth.sesion_de(peticion)}


@app.get("/api/cuentas-demo")
def cuentas_demo():
    """Las credenciales de demostración, para mostrarlas en la pantalla de entrada."""
    return auth.cuentas_demo()


@app.get("/api/salud")
def salud():
    return {"estado": "en pie", "front": DIST.exists()}


# Las rutas que usan el modelo van en su propio modulo. Se registran despues de
# las de sesion y antes del front, porque la ruta comodin de abajo se traga
# todo lo que no se haya declarado ya.
prediccion.registrar(app)


# ===========================================================================
# El front
#
# Va de último a propósito: cualquier ruta que no empiece por /api se resuelve
# con el index.html de React, que es quien decide qué pantalla mostrar. Si el
# build no existe todavía (desarrollo), se avisa en vez de devolver un 404 seco.
# ===========================================================================

if (DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")


@app.get("/{resto:path}")
def servir_front(resto: str):
    if resto.startswith("api/"):
        return JSONResponse({"detail": "No encontramos esa ruta."}, status_code=404)

    archivo = DIST / resto
    if resto and archivo.is_file():
        return FileResponse(archivo)

    indice = DIST / "index.html"
    if indice.is_file():
        return FileResponse(indice)

    return JSONResponse(
        {
            "detail": (
                "El front no está construido. En desarrollo use 'npm run dev' "
                "dentro de web/; para producción, 'npm run build'."
            )
        },
        status_code=503,
    )
