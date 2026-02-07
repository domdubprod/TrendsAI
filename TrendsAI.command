#!/bin/bash

# Este script permite iniciar TrendsAI con un doble clic en macOS.

# 1. Obtener el directorio donde se encuentra este archivo
cd "$(dirname "$0")"
echo "--- Iniciando TrendsAI Launcher ---"

# 2. Verificar dependencias e iniciar servicios usando el script central
# El script run.sh ya maneja la creación de venv y npm install
chmod +x run.sh

# Iniciamos el proceso en segundo plano para que podamos abrir el navegador
./run.sh &
RUN_PID=$!

# 3. Esperar a que el servidor esté arriba y abrir el navegador
echo "Esperando a que la aplicación esté lista..."
sleep 5
open "http://localhost:3000"

# Mantener la terminal abierta para ver logs y permitir cerrar con CTRL+C
echo "TrendsAI está corriendo. Pulsa Ctrl+C para detener."
wait $RUN_PID
