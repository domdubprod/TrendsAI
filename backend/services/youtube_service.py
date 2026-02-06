import os
import requests
import sqlite3
import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

class YouTubeService:
    def __init__(self, db_path: str = "backend/youtube_cache.db"):
        self.api_key = os.getenv("YOUTUBE_API_KEY")
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database for caching."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    timestamp DATETIME
                )
            """)
            conn.commit()

    def _get_cache(self, key: str) -> Optional[List[Dict[str, Any]]]:
        """Get value from SQLite cache if not expired (12 hours)."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value, timestamp FROM cache WHERE key = ?", (key,))
                row = cursor.fetchone()
                if row:
                    val, ts = row
                    cached_time = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                    if datetime.utcnow() - cached_time < timedelta(hours=12):
                        return json.loads(val)
                    else:
                        cursor.execute("DELETE FROM cache WHERE key = ?", (key,))
                        conn.commit()
        except Exception as e:
            print(f"Cache Load Error: {e}")
        return None

    def _set_cache(self, key: str, value: List[Dict[str, Any]]):
        """Save value to SQLite cache."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO cache (key, value, timestamp) VALUES (?, ?, ?)",
                    (key, json.dumps(value), datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
                )
                conn.commit()
        except Exception as e:
            print(f"Cache Save Error: {e}")

    def _call_with_backoff(self, url: str, params: Dict[str, Any], max_retries: int = 3) -> Any:
        """Execute request with exponential backoff."""
        for i in range(max_retries):
            try:
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code in [429, 500, 503]:
                    wait_time = (2 ** i) + (0.1 * i)
                    print(f"API Error {response.status_code}. Retrying in {wait_time:.2f}s...")
                    time.sleep(wait_time)
                else:
                    print(f"API Permanent Error ({response.status_code}): {response.text}")
                    return None
            except requests.exceptions.RequestException as e:
                wait_time = (2 ** i) + (0.1 * i)
                print(f"Request Exception: {e}. Retrying in {wait_time:.2f}s...")
                time.sleep(wait_time)
        return None

    def search_videos(self, query: str, time_filter: str = "7_days", video_type: str = "any", small_channels_only: bool = False, min_view_count: int = 0, max_view_count: int = 10000000, max_results: int = 50) -> List[Dict[str, Any]]:
        # 1. 2. 3. Check Persistent Cache (Include all filters in key)
        cache_key = f"{query}_{time_filter}_{video_type}_{small_channels_only}_{min_view_count}_{max_view_count}"
        cached_data = self._get_cache(cache_key)
        if cached_data:
            print(f"DEBUG: Serving '{cache_key}' from persistent cache.")
            return cached_data

        if not self.api_key:
            # ... (mock data logic remains same)
            print("WARNING: YOUTUBE_API_KEY not found. Returning mock data.")
            return self._get_mock_videos(query)

        # ... (Time filter logic remains same)
        # Mapping time_filter to publishedAfter and max_days
        now = datetime.utcnow()
        max_days = 7
        if time_filter == "hours":
            after = now - timedelta(hours=24)
            max_days = 1
        elif time_filter == "3_days":
            after = now - timedelta(days=3)
            max_days = 3
        elif time_filter == "month":
            after = now - timedelta(days=30)
            max_days = 30
        elif time_filter == "3_months":
            after = now - timedelta(days=90)
            max_days = 90
        elif time_filter == "7_months":
            after = now - timedelta(days=210)
            max_days = 210
        else: # Default 7 days
            after = now - timedelta(days=7)
            max_days = 7
            
        published_after = after.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        duration_map = {
            "shorts": "short",
            "normal": "medium"
        }
        yt_duration = duration_map.get(video_type)

        print(f"DEBUG: YouTube API Request - PublishedAfter: {published_after} | Duration: {yt_duration}")

        search_url = f"{self.base_url}/search"
        params = {
            "part": "snippet",
            "q": query,
            "maxResults": max_results,
            "type": "video",
            "order": "viewCount", 
            "publishedAfter": published_after,
            "relevanceLanguage": "es",
            "key": self.api_key,
            "fields": "items(id/videoId,snippet(title,channelId,channelTitle,publishedAt,thumbnails/high/url))"
        }
        
        if yt_duration:
            params["videoDuration"] = yt_duration

        data = self._call_with_backoff(search_url, params)
        if not data:
            return self._get_mock_videos(query)

        items = data.get("items", [])
        if not items:
            return []

        video_ids = [item["id"]["videoId"] for item in items]
        channel_ids = list(set([item["snippet"]["channelId"] for item in items if "channelId" in item["snippet"]]))
        
        # 2. Get Video & Channel Statistics
        video_stats = self.get_video_stats(video_ids)
        channel_stats = self.get_channel_stats(channel_ids)
        
        results = []
        for item in items:
            vid = item["id"]["videoId"]
            snippet = item["snippet"]
            cid = snippet.get("channelId")
            published_at = snippet.get("publishedAt")
            
            days_ago = 0
            if published_at:
                try:
                    pub_date = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
                    days_ago = (datetime.utcnow() - pub_date).days
                except: pass

            # STRICT FILTER
            if days_ago > max_days:
                continue

            # Stats extraction
            v_stats = video_stats.get(vid, {})
            c_stats = channel_stats.get(cid, {})
            
            view_count = int(v_stats.get("viewCount", 0))
            subscriber_count = int(c_stats.get("subscriberCount", 1)) # Prevent div by zero
            if subscriber_count == 0: subscriber_count = 1

            # --- VIEW COUNT RANGE FILTER ---
            if not (min_view_count <= view_count <= max_view_count):
                continue

            # --- VIRAL SCORE ALGORITHM ---
            viral_score = view_count / subscriber_count
            is_viral_gem = viral_score > 10
            
            # SMALL CHANNEL FILTER (< 1M Subs)
            if small_channels_only and subscriber_count > 1000000:
                continue

            results.append({
                "video_id": vid,
                "title": snippet.get("title"),
                "channel": snippet.get("channelTitle"),
                "channel_id": cid,
                "published_days_ago": days_ago,
                "view_count": view_count,
                "subscriber_count": subscriber_count,
                "viral_score": round(viral_score, 2),
                "is_viral_gem": is_viral_gem,
                "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url"),
                "video_url": f"https://www.youtube.com/watch?v={vid}"
            })
        
        
        # --- SORTING LOGIC ---
        # Prioritize Viral Score (High to Low), then View Count (High to Low)
        results.sort(key=lambda x: (x.get("viral_score", 0), x.get("view_count", 0)), reverse=True)
        
        final_results = results[:15] # Return top 15
        
        # 3. Save to Persistent Cache
        self._set_cache(cache_key, final_results)
        return final_results

    def get_channel_stats(self, channel_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Fetch subscriber count for channels."""
        if not self.api_key or not channel_ids:
            return {}

        stats_url = f"{self.base_url}/channels"
        # Split into chunks of 50 (YouTube API limit)
        all_stats = {}
        
        for i in range(0, len(channel_ids), 50):
            chunk = channel_ids[i:i+50]
            params = {
                "part": "statistics",
                "id": ",".join(chunk),
                "key": self.api_key,
                "fields": "items(id,statistics/subscriberCount)"
            }
            
            data = self._call_with_backoff(stats_url, params)
            if data and "items" in data:
                for item in data["items"]:
                    all_stats[item["id"]] = item["statistics"]
                    
        return all_stats

    def get_video_stats(self, video_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        if not self.api_key or not video_ids:
            return {}

        stats_url = f"{self.base_url}/videos"
        params = {
            "part": "statistics",
            "id": ",".join(video_ids),
            "key": self.api_key,
            "fields": "items(id,statistics/viewCount)"
        }

        data = self._call_with_backoff(stats_url, params)
        if not data:
            return {}

        items = data.get("items", [])
        return {item["id"]: item["statistics"] for item in items}

    def _get_mock_videos(self, query: str) -> List[Dict[str, Any]]:
        return [
            {
                "video_id": f"mock_{i}",
                "title": f"Video Viral sobre {query} #{i}",
                "channel": f"Creator {i}",
                "published_days_ago": i * 2,
                "view_count": 5000 * (10 - i),
                "thumbnail": "https://via.placeholder.com/480x360",
                "video_url": f"https://www.youtube.com/watch?v=mock_{i}"
            } for i in range(5)
        ]
