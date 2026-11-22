# -*- coding: utf-8 -*-
"""Asistente que traduce el resultado del modelo a lenguaje corriente.

Usa Gemini por su API REST, con la biblioteca estándar: no añade dependencias.

Sobre la clave: se lee de `st.secrets["GEMINI_API_KEY"]` y, en desarrollo, de la
variable de entorno del mismo nombre. Nunca se escribe en disco, ni se muestra, ni
aparece en ningún mensaje de error. Si no hay clave, el asistente se desactiva solo
y el resto de la aplicación sigue funcionando igual.

Qué se le manda al modelo de lenguaje: el riesgo estimado, el umbral, los factores
que más pesaron y las limitaciones conocidas del modelo. Nunca datos que
identifiquen a un paciente — en esta aplicación no existen, pero la regla se deja
escrita para cuando alguien conecte datos reales.
"""
from __future__ import annotations

import http.client
import json
import os
import socket
import ssl

# Streamlit solo hace falta para leer la clave de sus secretos. La API de
# FastAPI no lo instala, y entonces la clave se toma de la variable de entorno.
try:
    import streamlit as st
except ModuleNotFoundError:
    st = None

# Si el primero está sobrecargado (error 503, pasa a ratos) se prueba el siguiente.
# Para una demostración en vivo esto importa más que elegir el modelo perfecto.
MODELOS = ["gemini-flash-lite-latest", "gemini-flash-latest"]
SERVIDOR = "generativelanguage.googleapis.com"
RUTA = "/v1beta/models/{modelo}:generateContent"
TIEMPO_LIMITE = 25


class _ConexionIPv4(http.client.HTTPSConnection):
    """Conexión que resuelve el servidor solo por IPv4.

    En Streamlit Cloud la llamada se quedaba colgada hasta agotar el tiempo: el
    contenedor resuelve googleapis.com a una dirección IPv6 y no tiene ruta para
    salir por ahí, así que el intento no falla, simplemente no vuelve. Forzando
    IPv4 la conexión se establece de inmediato.

    El nombre del servidor se conserva para el SNI y la validación del
    certificado; lo único que cambia es la familia de direcciones.
    """

    def connect(self):
        familia, tipo, protocolo, _, direccion = socket.getaddrinfo(
            self.host, self.port, socket.AF_INET, socket.SOCK_STREAM)[0]
        bruto = socket.socket(familia, tipo, protocolo)
        bruto.settimeout(self.timeout)
        bruto.connect(direccion)
        contexto = self._context or ssl.create_default_context()
        self.sock = contexto.wrap_socket(bruto, server_hostname=self.host)

INSTRUCCIONES = """Eres el asistente de una aplicación académica que estima el riesgo
de que un paciente diabético vuelva a ser hospitalizado antes de 30 días.

Tu trabajo es explicarle el resultado a alguien que no sabe de modelos. Escribe en
español de Colombia, en segunda persona de usted, en máximo 150 palabras, sin viñetas
salvo que ayuden de verdad.

Reglas que no puedes romper:
- No eres un médico y no das consejo clínico. Si te lo piden, dilo con claridad.
- Nunca digas que el paciente "va a reingresar". Es una probabilidad, no un pronóstico.
- Si la probabilidad supera el umbral, eso solo significa que el paciente entra en la
  lista de seguimiento. Nunca significa que se le deba negar o restringir atención.
- Menciona, cuando venga al caso, que de cada 6 alertas solo 1 corresponde a un
  reingreso real. No lo escondas.
- No inventes cifras. Usa únicamente las que te den en el contexto.
- Si te preguntan algo que el contexto no responde, di que no lo sabes."""

LIMITES = """Limitaciones medidas de este modelo, que debes tener en cuenta:
- Detecta 6 de cada 10 reingresos reales, y solo 1 de cada 6 alertas acierta.
- Ese 6 de cada 10 es un promedio: entre pacientes transferidos a otra institución
  detecta 8,8 de cada 10, pero entre los que se van a su casa — el 79 % de los casos —
  solo 4,8 de cada 10.
- Alerta sobre el 51 % de los mayores de 80 años y sobre el 30 % de los menores de 50,
  aunque el riesgo real de ambos grupos es casi igual.
- Los datos son de hospitales de Estados Unidos entre 1999 y 2008.
- Es un prototipo académico, no está validado para uso clínico."""


def _clave():
    # El orden importa poco, pero la regla no: la clave no se escribe en disco,
    # no se muestra, y no aparece en ningun mensaje de error. Ni siquiera en el
    # cuerpo de un error de Gemini, que a veces la repite.
    if st is not None:
        try:
            if "GEMINI_API_KEY" in st.secrets:
                return st.secrets["GEMINI_API_KEY"]
        except Exception:
            pass
    return os.environ.get("GEMINI_API_KEY")


def disponible() -> bool:
    return bool(_clave())


def _contexto(estimacion) -> str:
    riesgo = estimacion["riesgo"]
    umbral = estimacion["umbral"]
    lineas = [
        f"Probabilidad estimada de reingreso antes de 30 días: {riesgo * 100:.1f} %.",
        f"Umbral de alerta del programa: {umbral * 100:.2f} %.",
        f"El paciente {'SÍ' if riesgo >= umbral else 'NO'} entra en la lista de seguimiento.",
        "Tasa general de reingreso en la cohorte de referencia: 11,4 %.",
        f"Este caso está {riesgo / 0.1139:.1f} veces esa tasa general.",
    ]
    if estimacion.get("efectos"):
        lineas.append("\nLo que más empuja este resultado, medido por el propio modelo:")
        for efecto in estimacion["efectos"][:5]:
            sentido = "sube" if efecto["efecto"] > 0 else "baja"
            lineas.append(
                f"- {efecto['nombre']}: {efecto['valor']} (lo típico es {efecto['tipico']}). "
                f"Este dato {sentido} el riesgo en {abs(efecto['efecto']) * 100:.1f} puntos; "
                f"sin él quedaría en {efecto['riesgo_sin_el'] * 100:.1f} %.")
    return "\n".join(lineas)


def responder(estimacion, pregunta: str) -> tuple[bool, str]:
    """Devuelve (hubo_respuesta, texto)."""
    clave = _clave()
    if not clave:
        return False, "No hay clave de Gemini configurada."

    cuerpo = {
        "systemInstruction": {"parts": [{"text": INSTRUCCIONES}]},
        "contents": [{"role": "user", "parts": [{"text":
            f"{LIMITES}\n\nResultado de este paciente:\n{_contexto(estimacion)}\n\n"
            f"Pregunta de quien está usando la aplicación:\n{pregunta}"}]}],
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 2000},
    }
    carga = json.dumps(cuerpo).encode("utf-8")
    cabeceras = {"Content-Type": "application/json", "x-goog-api-key": clave}
    datos, ultimo = None, "No se pudo contactar a Gemini."

    for modelo_nombre in MODELOS:
        conexion = None
        try:
            conexion = _ConexionIPv4(SERVIDOR, 443, timeout=TIEMPO_LIMITE)
            conexion.request("POST", RUTA.format(modelo=modelo_nombre), carga, cabeceras)
            respuesta = conexion.getresponse()
            crudo = respuesta.read()
            if respuesta.status == 200:
                datos = json.loads(crudo)
                break
            # solo el codigo: el cuerpo del error puede repetir la clave
            ultimo = f"Gemini respondió con un error {respuesta.status}."
            if respuesta.status not in (429, 500, 502, 503, 504):
                break
        except Exception as error:
            ultimo = f"No se pudo contactar a Gemini ({type(error).__name__})."
        finally:
            if conexion is not None:
                conexion.close()

    if datos is None:
        return False, ultimo

    try:
        partes = datos["candidates"][0]["content"]["parts"]
        texto = "".join(p.get("text", "") for p in partes).strip()
    except (KeyError, IndexError):
        return False, "Gemini no devolvió texto."
    return (True, texto) if texto else (False, "Gemini devolvió una respuesta vacía.")


SUGERENCIAS = [
    "Explíqueme este resultado como si yo no supiera nada de modelos.",
    "¿Qué debería hacer con este paciente?",
    "¿Qué tan confiable es este número?",
    "¿Por qué el modelo le da tanto peso a las hospitalizaciones previas?",
]
