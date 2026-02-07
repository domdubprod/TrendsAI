import os
import time
import sqlite3
import json
from typing import List, Optional
from datetime import datetime, timedelta
from pytrends.request import TrendReq
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

class TrendsService:
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Re-use the same database as YouTubeService
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.db_path = os.path.join(current_dir, "youtube_cache.db")
        else:
            self.db_path = db_path
            
        # hl='es-419' for Latin American Spanish, tz=360 (Mexico City/General GMT-6)
        self.pytrends = TrendReq(hl='es-419', tz=360, retries=2, backoff_factor=0.1, timeout=(10, 25))
        self._init_db()

    def _init_db(self):
        """Ensure the cache table exists (reused from YouTubeService db)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trends_cache (
                    keyword TEXT PRIMARY KEY,
                    results TEXT,
                    timestamp DATETIME
                )
            """)
            conn.commit()

    def _get_cached_trends(self, keyword: str) -> Optional[List[str]]:
        """Retrieve trends from SQLite cache if fresh (12h)."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT results, timestamp FROM trends_cache WHERE keyword = ?", (keyword.lower(),))
                row = cursor.fetchone()
                if row:
                    results, ts = row
                    cached_time = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                    if datetime.utcnow() - cached_time < timedelta(hours=12):
                        return json.loads(results)
        except Exception as e:
            print(f"Trends Cache Error: {e}")
        return None

    def _set_cached_trends(self, keyword: str, results: List[str]):
        """Save trends to SQLite cache."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO trends_cache (keyword, results, timestamp) VALUES (?, ?, ?)",
                    (keyword.lower(), json.dumps(results), datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
                )
                conn.commit()
        except Exception as e:
            print(f"Trends Cache Save Error: {e}")

    def get_rising_queries(self, niche: str) -> List[str]:
        """Fetch rising related queries from Google Trends (YouTube gprop)."""
        # 1. Check cache
        cached = self._get_cached_trends(niche)
        if cached:
            print(f"DEBUG: Trends for '{niche}' found in cache.")
            return cached

        # 2. Rate limit safety sleep (as requested by user)
        print(f"DEBUG: Fetching Trends for '{niche}' from Google... (Waiting 7s for rate limit safety)")
        time.sleep(7)

        try:
            # Simple keyword list for pytrends
            self.pytrends.build_payload([niche], cat=0, timeframe='today 3-m', geo='', gprop='youtube')
            
            related_queries = self.pytrends.related_queries()
            niche_trends = related_queries.get(niche, {})
            
            rising_df = niche_trends.get('rising')
            
            trends_found = []
            if rising_df is not None and not rising_df.empty:
                # Get top 5-10 rising queries
                trends_found = rising_df['query'].head(10).tolist()
            
            # 3. Fallback to 'top' if 'rising' is empty
            if not trends_found:
                top_df = niche_trends.get('top')
                if top_df is not None and not top_df.empty:
                    trends_found = top_df['query'].head(10).tolist()

            # 4. Cache and return
            self._set_cached_trends(niche, trends_found)
            return trends_found

        except Exception as e:
            print(f"PYTRENDS ERROR: {e}")
            return []
