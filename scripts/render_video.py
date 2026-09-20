"""
render_video.py — Renders news videos using FFmpeg.
Supports 3 styles:
  1. text_on_bg   — Bold Bangla/English text on a dark gradient background
  2. slideshow    — News thumbnail + animated text overlay
  3. audio_subs   — TTS audio (gTTS) + subtitle burn-in over a still image
"""

import os
import json
import subprocess
import textwrap
import requests
from pathlib import Path
from datetime import datetime

try:
    from gtts import gTTS
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

OUTPUT_DIR = Path("data/videos")
ASSETS_DIR = Path("assets")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

WATERMARK_TEXT = "Simply Reported"
FONT_PATH      = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
BANGLA_FONT    = "/usr/share/fonts/truetype/noto/NotoSansBengali-Bold.ttf"
VIDEO_W, VIDEO_H = 1920, 1080
FPS = 30
DURATION = 90   # seconds


def run_ffmpeg(cmd: list, label: str):
    print(f"  🎬 {label}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  [FFmpeg ERROR] {result.stderr[-500:]}")
        raise RuntimeError(f"FFmpeg failed: {label}")
    return result


def download_thumbnail(url: str, dest: Path) -> bool:
    """Download a thumbnail image from URL."""
    if not url:
        return False
    try:
        r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200 and len(r.content) > 1000:
            dest.write_bytes(r.content)
            return True
    except Exception as e:
        print(f"  [WARN] Thumbnail download failed: {e}")
    return False


def wrap_text(text: str, width: int = 40) -> str:
    """Wrap text for FFmpeg drawtext — use \\n as separator."""
    lines = textwrap.wrap(text, width=width)
    return "\\n".join(lines)


def style_text_on_bg(item_idx: int, content: dict) -> Path:
    """Style 1: Animated text on dark gradient background."""
    out_path = OUTPUT_DIR / f"video_{item_idx:03d}_textbg.mp4"
    src      = content["source_item"]
    title_bn = content.get("bangla_title", src["title"])
    script   = wrap_text(content.get("bangla_script", "")[:300], width=50)
    source   = src["source"]

    # gradient background via lavfi, then overlay text with fade animations
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c=0x0a0a1a:size={VIDEO_W}x{VIDEO_H}:rate={FPS}:duration={DURATION}",
        "-vf",
        (
            # dark-red accent bar at top
            f"drawbox=x=0:y=0:w={VIDEO_W}:h=8:color=0xcc0000:t=fill,"
            # channel source label
            f"drawtext=fontfile={FONT_PATH}:text='{source}':fontsize=36"
            f":fontcolor=0xcc0000:x=60:y=40:alpha='if(lt(t,1),0,if(lt(t,2),t-1,1))',"
            # main Bangla title — large
            f"drawtext=fontfile={FONT_PATH}:text='{title_bn[:60]}':fontsize=56"
            f":fontcolor=white:x=60:y=120:line_spacing=10"
            f":alpha='if(lt(t,1.5),0,if(lt(t,2.5),t-1.5,1))',"
            # divider
            f"drawbox=x=60:y=210:w=400:h=4:color=0xcc0000:t=fill,"
            # watermark bottom-right
            f"drawtext=fontfile={FONT_PATH}:text='{WATERMARK_TEXT}':fontsize=28"
            f":fontcolor=0xaaaaaa:x=w-tw-40:y=h-th-30,"
            # date stamp
            f"drawtext=fontfile={FONT_PATH}"
            f":text='{datetime.utcnow().strftime('%d %b %Y')}'"
            f":fontsize=26:fontcolor=0x888888:x=60:y=h-th-30"
        ),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-t", str(DURATION),
        str(out_path),
    ]
    run_ffmpeg(cmd, f"Style 1 (text-on-bg) → {out_path.name}")
    return out_path


def style_slideshow(item_idx: int, content: dict) -> Path | None:
    """Style 2: News thumbnail as background + text overlay."""
    src       = content["source_item"]
    thumb_url = src.get("thumbnail", "")
    thumb_dl  = OUTPUT_DIR / f"thumb_{item_idx:03d}.jpg"
    out_path  = OUTPUT_DIR / f"video_{item_idx:03d}_slideshow.mp4"

    if not download_thumbnail(thumb_url, thumb_dl):
        print(f"  [SKIP] No thumbnail for slideshow style — falling back to text-on-bg")
        return None

    title_bn = content.get("bangla_title", src["title"])
    caption  = content.get("facebook_caption_bangla", "")[:80]

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(thumb_dl),
        "-f", "lavfi", "-i", f"color=c=black:size={VIDEO_W}x{VIDEO_H}:rate={FPS}",
        "-filter_complex",
        (
            # scale thumbnail to fit, pad to 1920x1080
            f"[0:v]scale={VIDEO_W}:{VIDEO_H}:force_original_aspect_ratio=decrease,"
            f"pad={VIDEO_W}:{VIDEO_H}:(ow-iw)/2:(oh-ih)/2:black[scaled];"
            # dark overlay for readability
            f"[1:v]trim=duration={DURATION}[bg];"
            f"[bg][scaled]blend=all_expr='A*0.35+B*0.65'[blended];"
            # text overlays
            f"[blended]"
            f"drawbox=x=0:y=h-200:w=iw:h=200:color=black@0.7:t=fill,"
            f"drawtext=fontfile={FONT_PATH}:text='{title_bn[:55]}':fontsize=52"
            f":fontcolor=white:x=50:y=h-170:line_spacing=8,"
            f"drawtext=fontfile={FONT_PATH}:text='{caption}':fontsize=30"
            f":fontcolor=0xdddddd:x=50:y=h-60,"
            f"drawtext=fontfile={FONT_PATH}:text='{WATERMARK_TEXT}':fontsize=28"
            f":fontcolor=0xcc0000:x=w-tw-40:y=30[out]"
        ),
        "-map", "[out]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "22",
        "-t", str(DURATION),
        str(out_path),
    ]
    run_ffmpeg(cmd, f"Style 2 (slideshow) → {out_path.name}")
    return out_path


def style_audio_subs(item_idx: int, content: dict) -> Path | None:
    """Style 3: TTS audio + subtitle burn-in over thumbnail."""
    if not TTS_AVAILABLE:
        print("  [SKIP] gTTS not installed — skipping audio+subs style")
        return None

    src      = content["source_item"]
    script   = content.get("bangla_script", content.get("english_script", src["title"]))
    out_mp3  = OUTPUT_DIR / f"audio_{item_idx:03d}.mp3"
    out_srt  = OUTPUT_DIR / f"subs_{item_idx:03d}.srt"
    out_path = OUTPUT_DIR / f"video_{item_idx:03d}_audiosubs.mp4"
    thumb_dl = OUTPUT_DIR / f"thumb_{item_idx:03d}.jpg"

    # generate TTS
    try:
        lang = "bn"  # Bangla
        tts  = gTTS(text=script[:500], lang=lang, slow=False)
        tts.save(str(out_mp3))
    except Exception as e:
        print(f"  [WARN] TTS failed: {e}")
        return None

    # generate simple SRT subtitles (chunk script into lines)
    words     = script.split()
    chunk_sz  = 8
    chunks    = [" ".join(words[i:i+chunk_sz]) for i in range(0, len(words), chunk_sz)]
    secs_each = 90 / max(len(chunks), 1)
    srt_lines = []
    for i, chunk in enumerate(chunks):
        start = i * secs_each
        end   = start + secs_each
        srt_lines.append(
            f"{i+1}\n"
            f"{_fmt_srt_time(start)} --> {_fmt_srt_time(end)}\n"
            f"{chunk}\n"
        )
    out_srt.write_text("\n".join(srt_lines), encoding="utf-8")

    # background: thumbnail or black
    bg_input = str(thumb_dl) if thumb_dl.exists() else None
    if bg_input:
        input_args = ["-loop", "1", "-i", bg_input]
        vf = (
            f"scale={VIDEO_W}:{VIDEO_H}:force_original_aspect_ratio=decrease,"
            f"pad={VIDEO_W}:{VIDEO_H}:(ow-iw)/2:(oh-ih)/2:black,"
            f"subtitles={str(out_srt)}:force_style='FontName=DejaVu Sans,FontSize=24,"
            f"PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=2'"
        )
    else:
        input_args = ["-f", "lavfi", "-i", f"color=c=black:size={VIDEO_W}x{VIDEO_H}:rate={FPS}"]
        vf = (
            f"subtitles={str(out_srt)}:force_style='FontName=DejaVu Sans,FontSize=28,"
            f"PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=2'"
        )

    cmd = [
        "ffmpeg", "-y",
        *input_args,
        "-i", str(out_mp3),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", "22",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        str(out_path),
    ]
    run_ffmpeg(cmd, f"Style 3 (audio+subs) → {out_path.name}")
    return out_path


def _fmt_srt_time(seconds: float) -> str:
    h  = int(seconds // 3600)
    m  = int((seconds % 3600) // 60)
    s  = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def render_all_videos(generated_content: list[dict]) -> list[dict]:
    """Render all 3 styles for each generated content item."""
    rendered = []

    for idx, content in enumerate(generated_content):
        print(f"\n🎬 Rendering item {idx+1}/{len(generated_content)}: "
              f"{content['source_item']['source']}")

        item_videos = {"content": content, "videos": {}}

        v1 = style_text_on_bg(idx, content)
        if v1:
            item_videos["videos"]["text_on_bg"] = str(v1)

        v2 = style_slideshow(idx, content)
        if v2:
            item_videos["videos"]["slideshow"] = str(v2)

        v3 = style_audio_subs(idx, content)
        if v3:
            item_videos["videos"]["audio_subs"] = str(v3)

        rendered.append(item_videos)

    with open("data/rendered_videos.json", "w", encoding="utf-8") as f:
        json.dump(rendered, f, ensure_ascii=False, indent=2, default=str)

    return rendered


if __name__ == "__main__":
    with open("data/generated_content.json", encoding="utf-8") as f:
        data = json.load(f)
    render_all_videos(data["items"])
