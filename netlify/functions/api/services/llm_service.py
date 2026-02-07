# Load environment variables from the root directory if possible
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(BASE_DIR)))), ".env")
load_dotenv(ENV_PATH)
load_dotenv() # Fallback to local .env

class LLMService:
    def __init__(self):
        self.client = None
        self.gemini_model = None
        
        # 1. Try OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = OpenAI(api_key=api_key)
            print("INFO: LLMService using OpenAI (gpt-4o)")
        
        # 2. Try Gemini (Fallback or Primary)
        gemini_key = os.getenv("GOOGLE_GEMINI_API_KEY")
        if gemini_key:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            self.gemini_model = genai.GenerativeModel('gemini-2.5-flash')
            print("INFO: LLMService initialized Gemini support")
        
        self.system_role = (
            "Eres un analista de tendencias de contenido en YouTube especializado en detección temprana de oportunidades. "
            "Tu función no es listar datos, sino interpretarlos estratégicamente para creadores de contenido. "
            "Trabajas siempre en dos fases: "
            "1. Descubrimiento de palabras clave en tendencia a partir de un nicho. "
            "2. Análisis de videos relevantes a partir de una palabra clave seleccionada. "
            "Tomas decisiones basadas en relevancia semántica, crecimiento reciente y oportunidad, no solo en popularidad histórica."
        )

    async def generate_keywords(self, niche: str, trends_data: List[str] = None) -> Dict[str, Any]:
        """
        FASE 1: Generación de 6 keywords estratégicas basadas en el nicho y tendencias reales.
        """
        # Context building
        trend_context = ""
        if trends_data:
            trend_context = f"\nDatos de tendencias reales encontrados en Google Trends para este nicho:\n- " + "\n- ".join(trends_data)
        
        prompt = (
            f"Analiza el siguiente nicho: '{niche}'\n"
            f"{trend_context}\n\n"
            "Proceso:\n"
            "1. Identifica los ángulos más virales basándote en el nicho y las tendencias reales (si las hay) o tu conocimiento de tendencias actuales.\n"
            "2. Genera 6 keywords estratégicas únicas que tengan alto potencial de búsqueda.\n"
            "3. Mezcla términos específicos con variaciones long-tail.\n\n"
            "Responde ESTRICTAMENTE en JSON con este formato:\n"
            "{\n  \"keywords\": [\"k1\", \"k2\", \"k3\", \"k4\", \"k5\", \"k6\"]\n}"
        )

        # A. Try OpenAI
        if self.client:
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": self.system_role},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"}
                )
                return json.loads(response.choices[0].message.content)
            except Exception as e:
                print(f"Error en LLM OpenAI (Phase 1): {e}")

        # B. Try Gemini (if OpenAI failed or not configured)
        if self.gemini_model:
            for attempt in range(2):
                try:
                    print(f"DEBUG: Using Gemini for generate_keywords... (Attempt {attempt+1})")
                    response = self.gemini_model.generate_content(
                        f"{self.system_role}\n\nUSER PROMPT:\n{prompt}"
                    )
                    text = response.text.replace("```json", "").replace("```", "").strip()
                    return json.loads(text)
                except Exception as e:
                    if "429" in str(e) and attempt == 0:
                         print("WARNING: Gemini Rate Limit (429). Waiting 7s before retry...")
                         import time
                         time.sleep(7)
                         continue
                    print(f"Error en LLM Gemini (Phase 1): {e}")
                    break

        # C. Fallback to mock
        print("WARNING: No LLM available. Using mock data.")
        return self._get_dynamic_mock_keywords(niche, trends_data)

    async def analyze_videos(self, keyword: str, videos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        FASE 2: Análisis de videos reales obtenidos de la API.
        """
        video_context = json.dumps([{
            "title": v['title'],
            "views": v['view_count'],
            "days_ago": v['published_days_ago']
        } for v in videos], indent=2)

        prompt = (
            f"Analiza estos videos para la keyword: '{keyword}'\n\n"
            f"Datos:\n{video_context}\n\n"
            "Determina la oportunidad estratégica (alta | media | emergente) de cada uno.\n"
            "Responde en JSON:\n"
            "{\n  \"keyword\": \"...\",\n  \"videos\": [ { \"title\": \"...\", \"estimated_trend\": \"...\" } ]\n}"
        )

        # A. Try OpenAI
        if self.client:
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": self.system_role},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"}
                )
                return json.loads(response.choices[0].message.content)
            except Exception as e:
                print(f"Error en LLM OpenAI (Phase 2): {e}")

        # B. Try Gemini
        if self.gemini_model:
            try:
                print("DEBUG: Using Gemini for analyze_videos...")
                response = self.gemini_model.generate_content(
                    f"{self.system_role}\n\nUSER PROMPT:\n{prompt}"
                )
                text = response.text.replace("```json", "").replace("```", "").strip()
                return json.loads(text)
            except Exception as e:
                print(f"Error en LLM Gemini (Phase 2): {e}")

        # C. Fallback logic
        analyzed = []
        for v in videos:
            ratio = v['view_count'] / (v['published_days_ago'] + 1)
            trend = "alta" if ratio > 1000 else "media" if ratio > 100 else "emergente"
            analyzed.append({
                "title": v['title'],
                "channel": v['channel'],
                "published_days_ago": v['published_days_ago'],
                "estimated_trend": trend
            })
        return {"keyword": keyword, "videos": analyzed}

    def _get_dynamic_mock_keywords(self, niche: str, trends_data: List[str] = None) -> Dict[str, Any]:
        if trends_data:
            # Si tenemos tendencias reales, mezclarlas con el nicho
            results = []
            for trend in trends_data[:6]:
                results.append(trend.title())
            
            # Si faltan hasta llegar a 6, rellenar con variaciones del nicho
            if len(results) < 6:
                prefixes = ["Tendencias de", "Secretos de", "Guía para"]
                for p in prefixes:
                    if len(results) >= 6: break
                    results.append(f"{p} {niche}")
            return {"keywords": results[:6]}

        # Fallback si no hay ni tendencias ni LLM
        prefixes = ["Tendencias de", "Secretos de", "Guía para", "Evolución de", "Nicho: ", "Futuro de"]
        return {
            "keywords": [f"{p} {niche} {2026 if '2026' not in niche else ''}".strip() for p in prefixes]
        }
