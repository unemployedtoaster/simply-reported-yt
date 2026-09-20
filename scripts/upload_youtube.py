"""
upload_youtube.py — Uploads rendered videos to YouTube using Data API v3.
Uses OAuth2 service-account credentials stored as GitHub Secret.
"""

import os
import json
import time
import pickle
from pathlib import Path
from datetime import datetime

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

SCOPES      = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_FILE  = "data/youtube_token.pickle"
CREDS_ENV   = "YOUTUBE_OAUTH_CREDENTIALS"   # GitHub Secret name


def get_youtube_client():
    """Build authenticated YouTube client from stored OAuth2 credentials."""
    creds = None

    # Load credentials from env (JSON string stored as GitHub Secret)
    creds_json = os.environ.get(CREDS_ENV)
    if not creds_json:
        raise EnvironmentError(f"Missing secret: {CREDS_ENV}")

    creds_data = json.loads(creds_json)
    creds = Credentials(
        token         = creds_data.get("token"),
        refresh_token = creds_data["refresh_token"],
        token_uri     = creds_data.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id     = creds_data["client_id"],
        client_secret = creds_data["client_secret"],
        scopes        = SCOPES,
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    return build("youtube", "v3", credentials=creds)


def upload_video(youtube, video_path: str, content: dict, style: str) -> str | None:
    """Upload a single video file to YouTube."""
    src     = content["source_item"]
    title   = content.get("bangla_title", src["title"])[:100]
    desc_bn = content.get("youtube_description_bangla", "")
    desc_en = content.get("youtube_description_english", "")
    tags    = content.get("tags", [])
    source  = src["source"]

    description = f"""{desc_bn}

━━━━━━━━━━━━━━━━━━━━
{desc_en}

━━━━━━━━━━━━━━━━━━━━
Source: {source}
{src.get('video_url', src.get('url', ''))}

📺 Subscribe করুন Simply Reported: https://youtube.com/@simplyreported
📘 Facebook: https://facebook.com/simplyreported

#bangladesh #bdnews #বাংলাদেশ #SimplyReported
"""

    body = {
        "snippet": {
            "title":       f"{title} | {source} | Simply Reported",
            "description": description[:5000],
            "tags":        tags[:15],
            "categoryId":  "25",   # 25 = News & Politics
            "defaultLanguage":         "bn",
            "defaultAudioLanguage":    "bn",
        },
        "status": {
            "privacyStatus":  "public",
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        resumable=True,
        chunksize=1024 * 1024 * 5,   # 5 MB chunks
    )

    print(f"  ⬆️  Uploading: {Path(video_path).name}")
    try:
        request = youtube.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=media,
        )
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                pct = int(status.progress() * 100)
                print(f"     Progress: {pct}%", end="\r")
        video_id = response["id"]
        print(f"  ✅ Uploaded → https://youtu.be/{video_id}")
        return video_id
    except HttpError as e:
        print(f"  [ERROR] Upload failed: {e}")
        return None


def upload_all(rendered_videos: list[dict], max_uploads: int = 5) -> list[dict]:
    """Upload the best video style for each rendered item."""
    youtube  = get_youtube_client()
    uploaded = []
    count    = 0

    # Style priority: slideshow > audio_subs > text_on_bg
    STYLE_PRIORITY = ["slideshow", "audio_subs", "text_on_bg"]

    for item in rendered_videos:
        if count >= max_uploads:
            print(f"\n⚠️  Reached upload limit ({max_uploads}). Stopping.")
            break

        content = item["content"]
        videos  = item["videos"]

        chosen_path  = None
        chosen_style = None
        for style in STYLE_PRIORITY:
            if style in videos and Path(videos[style]).exists():
                chosen_path  = videos[style]
                chosen_style = style
                break

        if not chosen_path:
            print(f"  [SKIP] No video file found for: {content['source_item']['source']}")
            continue

        video_id = upload_video(youtube, chosen_path, content, chosen_style)
        if video_id:
            uploaded.append({
                "video_id":    video_id,
                "youtube_url": f"https://youtu.be/{video_id}",
                "title":       content.get("bangla_title", ""),
                "source":      content["source_item"]["source"],
                "style":       chosen_style,
                "uploaded_at": datetime.utcnow().isoformat(),
            })
            count += 1
            time.sleep(3)   # brief pause between uploads

    # save upload log
    log_path = Path("data/upload_log.json")
    existing = []
    if log_path.exists():
        with open(log_path, encoding="utf-8") as f:
            existing = json.load(f)
    existing.extend(uploaded)
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Uploaded {len(uploaded)} videos to YouTube")
    return uploaded


if __name__ == "__main__":
    with open("data/rendered_videos.json", encoding="utf-8") as f:
        rendered = json.load(f)
    upload_all(rendered)
