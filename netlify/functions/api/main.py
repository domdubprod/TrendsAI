import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from services.llm_service import LLMService
from services.youtube_service import YouTubeService
from services.trends_service import TrendsService
from services.gemini_service import GeminiService
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Robust .env discovery from project root
def load_root_env():
    curr = os.path.dirname(os.path.abspath(__file__))
    # Try multiple levels up to find the project root .env
    for _ in range(5):
        if os.path.exists(os.path.join(curr, ".env")):
            load_dotenv(os.path.join(curr, ".env"))
            print(f"INFO: Loaded environment from {os.path.join(curr, '.env')}")
            return
        curr = os.path.dirname(curr)
load_root_env()
load_dotenv() # Fallback

app = FastAPI(title="TrendsAI - Trend Engine")

# Add CORS middleware to allow frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the actual frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm_service = LLMService()
youtube_service = YouTubeService()
trends_service = TrendsService()
gemini_service = GeminiService()

class NicheRequest(BaseModel):
    niche: str

class AnalysisRequest(BaseModel):
    keyword: str
    time_filter: Optional[str] = "7_days"
    video_type: Optional[str] = "any"
    small_channels_only: Optional[bool] = False
    min_view_count: Optional[int] = 0
    max_view_count: Optional[int] = 10000000

@app.get("/")
async def root():
    return {"message": "TrendsAI Backend is running"}

@app.post("/api/discover")
async def discover_keywords(request: NicheRequest):
    """
    FASE 1: Descubrimiento de palabras clave en tendencia.
    """
    try:
        # 1. Fetch real trends from Google (YouTube gprop)
        real_trends = trends_service.get_rising_queries(request.niche)
        
        # 2. Generate keywords using LLM based on niche and trends
        result = await llm_service.generate_keywords(request.niche, real_trends)
        
        # 3. Add the original niche as the first option
        if "keywords" in result and isinstance(result["keywords"], list):
            result["keywords"].insert(0, request.niche)
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-viral-ideas")
async def generate_viral_ideas():
    """
    Generates 7 random viral keyword ideas using Google Gemini.
    """
    try:
        return await gemini_service.generate_viral_ideas()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze")
async def analyze_videos(request: AnalysisRequest):
    """
    FASE 2: Análisis de videos relevantes para una palabra clave.
    """
    try:
        # 1. Fetch real video data from YouTube with filters
        videos = youtube_service.search_videos(
            request.keyword, 
            time_filter=request.time_filter,
            video_type=request.video_type,
            small_channels_only=request.small_channels_only,
            min_view_count=request.min_view_count,
            max_view_count=request.max_view_count
        )
        
        # 2. Analyze videos using LLM logic
        analysis = await llm_service.analyze_videos(request.keyword, videos)
        
        # Merge original video data with AI analysis for the frontend
        analyzed_list = []
        analysis_map = {v["title"]: v["estimated_trend"] for v in analysis.get("videos", [])}
        
        for v in videos:
            analyzed_list.append({
                **v,
                "estimated_trend": analysis_map.get(v["title"], "emergente")
            })
            
        return {
            "keyword": request.keyword,
            "videos": analyzed_list
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
