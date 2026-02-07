#!/bin/bash

# Script para iniciar TrendsAI (Backend y Frontend) localmente

# 1. Configurar Backend (Python)
echo "--- Configurando Backend (Python) ---"
cd netlify/functions/api

if [ ! -d "venv" ]; then
    echo "Creando entorno virtual..."
    python3 -m venv venv
fi

echo "Instalando/Actualizando dependencias..."
./venv/bin/pip install -r requirements.txt

echo "Iniciando Backend (FastAPI) en puerto 8000..."
export PYTHONPATH=$PYTHONPATH:$(pwd)
./venv/bin/python3 main.py > backend.log 2>&1 &
BACKEND_PID=$!
sleep 2 # Darle un momento para iniciar

cd ../../../

# 2. Configurar Frontend (Node.js)
echo "--- Configurando Frontend (Node.js) ---"
cd frontend

if [ ! -d "node_modules" ]; then
    echo "Instalando dependencias de Node..."
    npm install
fi

echo "Iniciando Frontend (Vite) en puerto 3000..."
npm run dev -- --port 3000 --host 0.0.0.0

# Al cerrar el frontend, matamos el backend
trap "kill $BACKEND_PID" EXIT

