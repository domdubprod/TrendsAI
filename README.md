# TrendsAI - Local Setup Guide

TrendsAI es una herramienta inteligente para descubrir nichos y tendencias virales en YouTube. Este repositorio permite correr la aplicación localmente siguiendo estos pasos.

## Requisitos Previos

- **Python 3.9+**
- **Node.js 18+** y **npm**
- Una cuenta de **Google Cloud** para obtener las API Keys (opcional pero recomendado para datos reales).

## Configuración de Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto (o dentro de la carpeta `functions/`) con el siguiente contenido:

```env
GOOGLE_GEMINI_API_KEY=tu_api_key_aqui
YOUTUBE_API_KEY=tu_api_key_aqui
```

> [!NOTE]
> - Puedes obtener la `GOOGLE_GEMINI_API_KEY` en [Google AI Studio](https://aistudio.google.com/).
> - La `YOUTUBE_API_KEY` se obtiene en la [Google Cloud Console](https://console.cloud.google.com/), habilitando la "YouTube Data API v3".

## Cómo Correr la Aplicación

Hemos incluido scripts para facilitar el inicio:

### 1. Opción Rápida (Recomendada para macOS)
Doble clic en el archivo **`TrendsAI.command`**.
- Esto abrirá una terminal automáticamente.
- Instalará lo que falte (la primera vez).
- **Abrirá tu navegador** en `http://localhost:3000` cuando esté listo.

### 2. Opción por Terminal
Si prefieres usar la terminal:
1. Dale permisos de ejecución al script:
   ```bash
   chmod +x run.sh
   ```
2. Ejecuta el script:
   ```bash
   ./run.sh
   ```

Este script hará lo siguiente:
- Creará un entorno virtual de Python y descargará las dependencias.
- Iniciará el Backend (FastAPI) en `http://localhost:8000`.
- Instalará las dependencias de Node.js del Frontend.
- Iniciará el Frontend (Vite) en `http://localhost:3000`.

## Estructura del Proyecto

- `/functions`: Backend en Python (FastAPI).
- `/frontend`: Frontend en React (Vite + Tailwind/CSS).
- `run.sh`: Script de inicio rápido.
