"""
fetch_news.py — Fetches latest videos & articles from all major BD news sources
"""

import os
import json
import time
import requests
import feedparser
from datetime import datetime, timedelta
from googleapiclient.discovery import build

# ─── YouTube Channel IDs for major BD news channels ───────────────────────────
BD_YOUTUBE_CHANNELS = {
    "Jamuna TV":            "UCJ4xs3K8pGTuMFdEW5KDyZg",
    "Channel 24":           "UCefOFd_QnJn5-DeFFlNnGwQ",
    "Somoy TV":             "UCpbLBDKxGoXPrdD2SMb90Xw",
    "Ekattor TV":           "UCcBEedTkmnfGp7bMVXCdlxg",
    "NTV":                  "UCIHbAQCa0LjMiAezFr-DKZQ",
    "RTV News":             "UCqsZ9GCIe_0RLCNZ0NrXvNw",
    "Independent TV":       "UCUmDOFqS4XBe-K5q_3KThew",
    "ATN News":             "UCxB3YD8XKNJHZ0bm5QHYkxQ",
    "DBC News":             "UCxw3VJW4WcFOKWxApBSqqZw",
    "Banglavision News":    "UCOi7dwKkY8MPGA14PJkzQmA",
    "News24 Bangladesh":    "UC2Hq5oA8bqoQwqC-kgRWzXg",
}

# ─── RSS feeds for BD online news portals ─────────────────────────────────────
BD_RSS_FEEDS = {
    "Prothom Alo":   "https://www.prothomalo.com/feed/",
    "Daily Star":    "https://www.thedailystar.net/rss.xml",
    "bdnews24":      "https://bdnews24.com/rss",
    "Janobani":      "https://www.janobani.com/feed/",
    "Jugantor":      "https://www.jugantor.com/rss.xml",
    "Kaler Kantho":  "https://www.kalerkantho.com/rss.xml",
    "Samakal":       "https://samakal.com/rss.xml",
    "Manabzamin":    "https://mzamin.com/rss.xml",
    "Ittefaq":       "https://www.ittefaq.com.bd/feed/",
    "Bangladesh Pratidin": "https://www.bd-pratidin.com/rss.xml",
    "Dhaka Tribune": "https://www.dhakatribune.com/feed",
    "New Age BD":    "https://www.newagebd.net/rss.xml",
}

MAX_VIDEOS_PER_CHANNEL = 3
MAX_ARTICLES_PER_FEED  = 2
HOURS_LOOKBACK         = 24


def get_recent_youtube_videos(api_key: str) -> list[dict]:
    """Fetch recent videos from all BD YouTube news channels."""
    youtube  = build("youtube", "v3", developerKey=api_key)
    cutoff   = datetime.utcnow() - timedelta(hours=HOURS_LOOKBACK)
    cutoff_s = cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")
    videos   = []

    for channel_name, channel_id in BD_YOUTUBE_CHANNELS.items():
        try:
            resp = youtube.search().list(
                channelId=channel_id,
                part="snippet",
                order="date",
                type="video",
                publishedAfter=cutoff_s,
                maxResults=MAX_VIDEOS_PER_CHANNEL,
            ).execute()

            for item in resp.get("items", []):
                snippet   = item["snippet"]
                video_id  = item["id"]["videoId"]
                videos.append({
                    "source":       channel_name,
                    "type":         "youtube_video",
                    "title":        snippet["title"],
                    "description":  snippet.get("description", ""),
                    "thumbnail":    snippet["thumbnails"]["high"]["url"],
                    "video_id":     video_id,
                    "video_url":    f"https://www.youtube.com/watch?v={video_id}",
                    "published_at": snippet["publishedAt"],
                    "channel_id":   channel_id,
                })
            time.sleep(0.5)   # gentle rate limit
        except Exception as e:
            print(f"[WARN] YouTube fetch failed for {channel_name}: {e}")

    return videos


def get_recent_rss_articles() -> list[dict]:
    """Fetch recent articles from BD news RSS feeds."""
    articles = []
    cutoff   = datetime.utcnow() - timedelta(hours=HOURS_LOOKBACK)

    for source_name, feed_url in BD_RSS_FEEDS.items():
        try:
            feed  = feedparser.parse(feed_url)
            count = 0
            for entry in feed.entries:
                if count >= MAX_ARTICLES_PER_FEED:
                    break
                # parse publish date
                published = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6])
                    if published < cutoff:
                        continue

                thumbnail = ""
                if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
                    thumbnail = entry.media_thumbnail[0].get("url", "")
                elif hasattr(entry, "media_content") and entry.media_content:
                    thumbnail = entry.media_content[0].get("url", "")

                articles.append({
                    "source":       source_name,
                    "type":         "article",
                    "title":        entry.get("title", ""),
                    "description":  entry.get("summary", "")[:500],
                    "thumbnail":    thumbnail,
                    "url":          entry.get("link", ""),
                    "published_at": published.isoformat() if published else "",
                })
                count += 1
            time.sleep(0.3)
        except Exception as e:
            print(f"[WARN] RSS fetch failed for {source_name}: {e}")

    return articles


def fetch_all_news(youtube_api_key: str) -> dict:
    print("📡 Fetching YouTube videos from BD news channels...")
    videos   = get_recent_youtube_videos(youtube_api_key)
    print(f"   ✅ Got {len(videos)} videos")

    print("📰 Fetching RSS articles from BD news portals...")
    articles = get_recent_rss_articles()
    print(f"   ✅ Got {len(articles)} articles")

    result = {
        "fetched_at": datetime.utcnow().isoformat(),
        "videos":     videos,
        "articles":   articles,
        "total":      len(videos) + len(articles),
    }

    os.makedirs("data", exist_ok=True)
    with open("data/news_raw.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Total items fetched: {result['total']}")
    return result


if __name__ == "__main__":
    key = os.environ["YOUTUBE_API_KEY"]
    fetch_all_news(key)
