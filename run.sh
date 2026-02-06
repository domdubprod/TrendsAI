#!/bin/bash

# Script para iniciar TrendsAI (Backend y Frontend)

# 1. Iniciar Backend en segundo plano
echo "Iniciando Backend (FastAPI)..."
source backend/venv/bin/activate
export PYTHONPATH=$PYTHONPATH:$(pwd)
python3 backend/main.py &
BACKEND_PID=$!

# 2. Iniciar Frontend
echo "Iniciando Frontend (Vite)..."
cd frontend
npm run dev -- --port 3000

# Al cerrar el frontend, matamos el backend
trap "kill $BACKEND_PID" EXIT
