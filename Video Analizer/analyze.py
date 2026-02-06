import os
import sys
import time
import json
import re
from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
from dotenv import load_dotenv
import yt_dlp

# Load environment variables
load_dotenv()

# Configure Gemini
api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
if not api_key:
    print("Error: GOOGLE_GEMINI_API_KEY not found in environment.")
    sys.exit(1)

genai.configure(api_key=api_key)

# Initialize Model
MODEL_NAME = 'gemini-2.5-flash' 
model = genai.GenerativeModel(MODEL_NAME)

ANALYSIS_SYSTEM_PROMPT = """
Rol: Actúa como un experto en estrategia de contenido digital y analista de algoritmos de YouTube.

Tarea: Analiza el video de YouTube proporcionado y genera un informe técnico detallado extrayendo los siguientes puntos:

1. Título: Identifica el título original y propón una variante más optimizada para CTR.
2. Contexto: ¿De qué trata el video a nivel general? (Nicho y propósito).
3. Estilo de Video: (Ej: Documental, Vlog, Tutorial, Ensayo visual, Gaming).
4. Personajes: Identifica al presentador y otros participantes relevantes.
5. Ambiente: Describe el entorno físico o digital donde ocurre la acción.
6. Música: Describe el tipo de banda sonora (tonalidad, ritmo y cómo afecta al mood).
7. Hook (Gancho): Identifica los primeros 30 segundos. ¿Cómo retiene la atención inicial?
8. Estructura: Desglose por tiempos o capítulos del video.
9. Guion: Resumen narrativo de los puntos clave tratados.
10. Idioma: Identifica el idioma principal y si hay modismos específicos.
11. Factor de Viralidad: Analiza por qué este video funciona. Evalúa el "retention craft", el valor emocional o la utilidad técnica que lo hace compartible.

Formato de salida: Utiliza Markdown con encabezados claros y puntos de viñeta.
"""

def extract_video_id(url: str) -> Optional[str]:
    """Extracts YouTube Video ID from various URL formats."""
    parsed = urlparse(url)
    if parsed.hostname in ('youtu.be', 'www.youtu.be'):
        return parsed.path[1:]
    if parsed.hostname in ('youtube.com', 'www.youtube.com'):
        if parsed.path == '/watch':
            return parse_qs(parsed.query)['v'][0]
        if parsed.path.startswith('/embed/'):
            return parsed.path.split('/')[2]
        if parsed.path.startswith('/v/'):
            return parsed.path.split('/')[2]
    return None

def get_transcript(video_id: str) -> str:
    """Fetches transcript for the video."""
    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.fetch(video_id)
        
        full_text = ""
        for entry in transcript_list:
            start = int(entry.get('start', 0))
            minutes = start // 60
            seconds = start % 60
            timestamp = f"[{minutes:02d}:{seconds:02d}]"
            full_text += f"{timestamp} {entry.get('text', '')} "
        
        return full_text
    except Exception as e:
        print(f"Warning: Could not fetch transcript ({e}). Switching to Video Analysis.")
        return ""

def download_video(url: str, output_path: str) -> bool:
    """Downloads video using yt-dlp to the specified path."""
    ydl_opts = {
        'format': 'worst[ext=mp4]', 
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
        # Valid user agent to avoid 403
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.youtube.com/',
        }
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True
    except Exception as e:
        print(f"Error downloading video: {e}")
        return False

def upload_and_process_video(video_path: str):
    """Uploads video to Gemini File API and waits for processing."""
    print("Uploading video to Gemini...")
    video_file = genai.upload_file(video_path)
    print(f"Upload complete. URI: {video_file.uri}")

    # Verify state
    while video_file.state.name == "PROCESSING":
        print('.', end='', flush=True)
        time.sleep(2)
        video_file = genai.get_file(video_file.name)

    if video_file.state.name == "FAILED":
        raise ValueError("Video processing failed.")
    
    print("\nVideo processed successfully.")
    return video_file

def analyze_video(url: str):
    print(f"--- Analyzing Video: {url} ---")
    
    video_id = extract_video_id(url)
    if not video_id:
        print("Error: Could not extract Video ID from URL.")
        return

    print(f"Video ID: {video_id}")
    
    # 1. Try Transcript first (Fastest/Cheapest)
    print("Step 1: Attempting to fetch transcript...")
    transcript_text = get_transcript(video_id)
    
    prompt_content = []

    if transcript_text:
        print(f"Transcript fetched successfully ({len(transcript_text)} chars).")
        prompt_content = [
            f"URL del Video: {url}",
            f"TRANSCRIPCIÓN:\n{transcript_text[:100000]}",
            ANALYSIS_SYSTEM_PROMPT
        ]
    else:
        # 2. Fallback: Multimodal Video Analysis
        print("Transcript unavailable. Starting Multimodal Video Analysis (Download & Watch)...")
        video_filename = f"temp_{video_id}.mp4"
        
        if download_video(url, video_filename):
            try:
                video_file_handle = upload_and_process_video(video_filename)
                
                print("Analyzing video content with Gemini (Multimodal)...")
                prompt_content = [
                    video_file_handle,
                    ANALYSIS_SYSTEM_PROMPT
                ]
            except Exception as e:
                print(f"Error during video processing: {e}")
                if os.path.exists(video_filename):
                    os.remove(video_filename)
                return
        else:
            print("Failed to download video. Cannot proceed.")
            return

    # 3. Generate Content
    try:
        response = model.generate_content(prompt_content)
        report = response.text
        
        # Output
        output_filename = f"analysis_{video_id}.md"
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(report)
            
        print("\n" + "="*50)
        print(report)
        print("="*50)
        print(f"\nReport saved to: {os.path.abspath(output_filename)}")

    except Exception as e:
        print(f"Error during AI analysis generation: {e}")
    finally:
        # Cleanup video file if it exists
        if 'video_filename' in locals() and os.path.exists(video_filename):
            os.remove(video_filename)
            print("Temporary video file cleaned up.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze.py <youtube_url>")
        sys.exit(1)
    
    video_url = sys.argv[1]
    # Simple check to strip markdown links if user pasted [url](url)
    if "](" in video_url:
        video_url = video_url.split("](")[1].rstrip(")")
        
    analyze_video(video_url)
