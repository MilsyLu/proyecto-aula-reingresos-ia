#!/usr/bin/env bash
# Prepara el servidor para ReingresaIA. Se corre una sola vez.
#
#   bash despliegue/preparar.sh
#
# Hace tres cosas y ninguna toca RustDesk:
#   1. Abre los puertos 80 y 443 en el cortafuegos del servidor.
#   2. Genera la clave que firma las cookies de sesion.
#   3. Deja escrito el dominio, derivado de la IP publica con sslip.io.
#
# Lo que este script NO puede hacer es abrir los puertos en la consola de
# Oracle: eso vive fuera del servidor. Si los paquetes no llegan ni siquiera
# al cortafuegos, revise primero la lista de seguridad de la red virtual.

set -euo pipefail

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENTORNO="$AQUI/.env"

echo "== 1. Cortafuegos del servidor =="

# Las reglas se insertan ANTES del REJECT final; si se anadieran al final no
# servirian de nada, porque el REJECT ya habria descartado el paquete.
posicion_rechazo() {
	sudo iptables -L INPUT -n --line-numbers | awk '$2 == "REJECT" {print $1; exit}'
}

abrir_puerto() {
	local puerto="$1"
	if sudo iptables -C INPUT -p tcp --dport "$puerto" -m state --state NEW -j ACCEPT 2>/dev/null; then
		echo "   puerto $puerto: ya estaba abierto"
		return
	fi
	local rechazo
	rechazo="$(posicion_rechazo || true)"
	if [ -n "$rechazo" ]; then
		sudo iptables -I INPUT "$rechazo" -p tcp --dport "$puerto" -m state --state NEW -j ACCEPT
	else
		sudo iptables -A INPUT -p tcp --dport "$puerto" -m state --state NEW -j ACCEPT
	fi
	echo "   puerto $puerto: abierto"
}

abrir_puerto 80
abrir_puerto 443

# Sin esto las reglas se pierden al reiniciar el servidor.
if command -v netfilter-persistent >/dev/null 2>&1; then
	sudo netfilter-persistent save >/dev/null && echo "   reglas guardadas"
else
	echo "   AVISO: no hay netfilter-persistent; las reglas se pierden al reiniciar."
	echo "   Instalelo con: sudo apt-get install -y iptables-persistent"
fi

echo
echo "== 2. Dominio =="

IP="$(curl -s --max-time 10 https://api.ipify.org || true)"
if [ -z "$IP" ]; then
	echo "   No se pudo averiguar la IP publica. Escribala a mano en $ENTORNO"
	exit 1
fi
# sslip.io resuelve cualquier nombre con la IP dentro, sin cuenta ni token.
DOMINIO="${IP//./-}.sslip.io"
echo "   IP publica: $IP"
echo "   dominio:    $DOMINIO"

echo
echo "== 3. Clave de sesion =="

if [ -f "$ENTORNO" ] && grep -q '^REINGRESAIA_CLAVE_SESION=' "$ENTORNO"; then
	echo "   ya existe, se conserva (cambiarla cerraria todas las sesiones)"
	CLAVE="$(grep '^REINGRESAIA_CLAVE_SESION=' "$ENTORNO" | cut -d= -f2-)"
else
	CLAVE="$(head -c 32 /dev/urandom | base64 | tr -d '/+=' | head -c 43)"
	echo "   generada"
fi

umask 077
cat >"$ENTORNO" <<FIN
# Generado por preparar.sh. No se versiona ni se comparte.
REINGRESAIA_CLAVE_SESION=$CLAVE
DOMINIO=$DOMINIO
FIN
chmod 600 "$ENTORNO"
echo "   guardada en $ENTORNO (solo lectura para el dueno)"

echo
echo "Listo. Ahora:"
echo "   cd $AQUI && sudo docker compose up -d --build"
echo
echo "Cuando termine, la aplicacion queda en:  https://$DOMINIO"
echo
echo "Si el navegador no carga nada, el cortafuegos del servidor no es el"
echo "problema: faltan los puertos 80 y 443 en la lista de seguridad de"
echo "Oracle, que se abre desde la consola web."
