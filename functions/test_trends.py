import sys
import os
import asyncio
from typing import List

# Add root directory to sys.path
sys.path.append(os.getcwd())

from backend.services.trends_service import TrendsService
from backend.services.llm_service import LLMService

async def test_trends_integration():
    niche = "Gaming"
    print(f"--- Testing Trends Integration for Niche: '{niche}' ---")
    
    trends_service = TrendsService(db_path="backend/youtube_cache.db")
    llm_service = LLMService()
    
    # 1. Test TrendsService directly
    print("\n1. Fetching Rising Queries from Google Trends...")
    real_trends = trends_service.get_rising_queries(niche)
    print(f"Found Trends: {real_trends}")
    
    if not real_trends:
        print("Warning: No trends found. Check network connection or niche popularity.")
    
    # 2. Test LLMService with Trends context
    print("\n2. Generating Keywords via LLM with Trends Context...")
    result = await llm_service.generate_keywords(niche, real_trends)
    print(f"Generated Keywords: {result.get('keywords', [])}")
    
    # 3. Verify uniqueness and diversity
    keywords = result.get('keywords', [])
    if len(keywords) == 6:
        print("\nSUCCESS: 6 strategic keywords generated.")
    else:
        print(f"\nFAILURE: Expected 6 keywords, got {len(keywords)}.")

if __name__ == "__main__":
    asyncio.run(test_trends_integration())
