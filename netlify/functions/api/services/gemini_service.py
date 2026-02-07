import os
import json
import google.generativeai as genai
from typing import List, Dict
from dotenv import load_dotenv

# Robust .env discovery
def load_root_env():
    curr = os.path.dirname(os.path.abspath(__file__))
    for _ in range(5):
        if os.path.exists(os.path.join(curr, ".env")):
            load_dotenv(os.path.join(curr, ".env"))
            return
        curr = os.path.dirname(curr)
load_root_env()
load_dotenv() # Fallback

class GeminiService:
    def __init__(self):
        api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
        if not api_key:
            print("WARNING: GOOGLE_GEMINI_API_KEY not found.")
            self.model = None
        else:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')

    async def generate_viral_ideas(self) -> Dict[str, List[str]]:
        """
        Generates 7 random, high-potential viral video keywords/topics.
        """
        if not self.model:
            return {"keywords": ["No API Key Configured"]}

        prompt = (
            "Actúa como un experto en tendencias virales de YouTube. "
            "Genera una lista de 7 ideas o palabras clave únicas para videos altamente virales. "
            "Piensa en tendencias globales, misterios, tecnología, desafíos o temas evergreen que siempre funcionan. "
            "Devuelve SOLO una lista JSON de strings, sin markdown ni explicaciones adicionales. "
            "Ejemplo de formato: [\"Idea 1\", \"Idea 2\", ...]"
        )

        try:
            response = self.model.generate_content(prompt)
            # Clean possible markdown code blocks
            text = response.text.replace("```json", "").replace("```", "").strip()
            keywords = json.loads(text)
            
            # Ensure it's a list of 7 items
            return {"keywords": keywords[:7]}
        except Exception as e:
            print(f"Error generating viral ideas with Gemini: {e}")
            return {"keywords": [
                "Misterios sin resolver 2026",
                "Gadgets tecnológicos baratos",
                "Experimentos sociales impactantes",
                "Historias de terror reales",
                "Desafíos de comida gigantes",
                "Transformaciones físicas extremas",
                "Secretos de millonarios"
            ]}
