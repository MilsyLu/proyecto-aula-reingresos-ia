#!/usr/bin/env bash
# Quien puede entrar a ReingresaIA.
#
#   bash despliegue/acceso.sh colombia   solo desde Colombia (lo normal)
#   bash despliegue/acceso.sh todos      desde cualquier parte del mundo
#   bash despliegue/acceso.sh cerrado    nadie, ni siquiera desde Colombia
#   bash despliegue/acceso.sh estado     que hay puesto ahora mismo
#
# Reutiliza las listas `colombia` y `excepciones` que ya existen en el
# servidor por SoporteDesk: 2.020 redes de LACNIC y DB-IP, mas las que se
# hayan agregado a mano. No crea listas nuevas ni toca las reglas de RustDesk.
#
# EL PUERTO 80 SIEMPRE QUEDA ABIERTO cuando hay acceso, y no es un descuido.
# Let's Encrypt valida el certificado desde servidores que no estan en
# Colombia; si se filtra el 80, el certificado no se emite ni se renueva y el
# navegador muestra advertencia de sitio inseguro. En el 80 solo vive esa
# validacion y una redireccion a HTTPS: la aplicacion se sirve por el 443,
# que si queda filtrado.
#
# Para cerrarlo todo despues de la sustentacion:  acceso.sh cerrado

set -euo pipefail

MODO="${1:-estado}"

posicion_rechazo() {
	sudo iptables -L INPUT -n --line-numbers | awk '$2 == "REJECT" {print $1; exit}'
}

# Quita cualquier regla previa de 80/443 para que no se acumulen al repetir.
limpiar() {
	local puerto
	for puerto in 80 443; do
		while sudo iptables -L INPUT -n --line-numbers \
			| awk -v p="dpt:$puerto" '$0 ~ p {print $1; exit}' \
			| grep -q .; do
			local linea
			linea="$(sudo iptables -L INPUT -n --line-numbers | awk -v p="dpt:$puerto" '$0 ~ p {print $1; exit}')"
			sudo iptables -D INPUT "$linea"
		done
	done
}

insertar() {
	local rechazo
	rechazo="$(posicion_rechazo || true)"
	if [ -n "$rechazo" ]; then
		sudo iptables -I INPUT "$rechazo" "$@"
	else
		sudo iptables -A INPUT "$@"
	fi
}

guardar() {
	if command -v netfilter-persistent >/dev/null 2>&1; then
		sudo netfilter-persistent save >/dev/null 2>&1 && echo "   reglas guardadas (sobreviven a un reinicio)"
	else
		echo "   AVISO: sin netfilter-persistent, esto se pierde al reiniciar"
	fi
}

mostrar_estado() {
	echo "Reglas activas para los puertos de la aplicacion:"
	sudo iptables -L INPUT -n --line-numbers | awk 'NR<=2 || /dpt:(80|443)|dports 80|dports 443/'
	echo
	if sudo iptables -L INPUT -n | grep -q 'dpt:443'; then
		if sudo iptables -L INPUT -n | grep 'dpt:443' | grep -q 'match-set'; then
			echo "ESTADO: abierto solo desde Colombia"
		else
			echo "ESTADO: abierto a todo internet"
		fi
	else
		echo "ESTADO: cerrado, nadie puede entrar"
	fi
}

case "$MODO" in
colombia)
	echo "== Acceso solo desde Colombia =="
	limpiar
	# 80 abierto para que Let's Encrypt pueda validar y renovar.
	insertar -p tcp --dport 80 -m state --state NEW -j ACCEPT
	# 443, que es donde vive la aplicacion, solo para las dos listas.
	insertar -p tcp --dport 443 -m set --match-set colombia src -m state --state NEW -j ACCEPT
	insertar -p tcp --dport 443 -m set --match-set excepciones src -m state --state NEW -j ACCEPT
	echo "   puerto 80:  abierto (solo validacion del certificado y redireccion)"
	echo "   puerto 443: solo Colombia y excepciones"
	guardar
	echo
	echo "Si alguien en Colombia no puede entrar, su operador puede estar usando"
	echo "direcciones de fuera de la region. Agreguelo a mano con:"
	echo "   sudo ipset add excepciones LA.DIRECCION.IP.AQUI"
	;;
todos)
	echo "== Acceso desde cualquier parte =="
	limpiar
	insertar -p tcp --dport 80 -m state --state NEW -j ACCEPT
	insertar -p tcp --dport 443 -m state --state NEW -j ACCEPT
	echo "   puertos 80 y 443 abiertos a todo internet"
	guardar
	;;
cerrado)
	echo "== Acceso cerrado =="
	limpiar
	echo "   puertos 80 y 443 cerrados"
	guardar
	echo
	echo "La aplicacion sigue corriendo por dentro. Para apagarla del todo:"
	echo "   cd ~/reingresaia/despliegue && sudo docker compose down"
	echo
	echo "RustDesk no se toco y sigue funcionando."
	;;
estado)
	mostrar_estado
	;;
*)
	echo "Uso: acceso.sh [colombia|todos|cerrado|estado]" >&2
	exit 1
	;;
esac
