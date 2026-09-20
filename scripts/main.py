"""
main.py — Orchestrates the full pipeline:
  1. Fetch news from all BD sources
  2. Generate scripts/titles/tags with Groq
  3. Render videos with FFmpeg
  4. Upload to YouTube (or save locally in test mode)
"""

import os
import sys
import json
import argparse
from pathlib import Path

def run_pipeline(args):
    print("=" * 60)
    print("  🇧🇩 Simply Reported — BD News Auto-Publisher")
    if args.test:
        print("  🧪 TEST MODE — videos will be saved, not uploaded")
    print("=" * 60)

    # ── Step 1: Fetch news ───────────────────────────────────────
    if not args.skip_fetch:
        print("\n📡 STEP 1: Fetching news...")
        from scripts.fetch_news import fetch_all_news
        news = fetch_all_news(os.environ["YOUTUBE_API_KEY"])
    else:
        print("\n📡 STEP 1: Loading cached news...")
        with open("data/news_raw.json", encoding="utf-8") as f:
            news = json.load(f)
    print(f"   Total items: {news['total']}")

    # ── Step 2: Generate content with Groq ───────────────────────
    if not args.skip_generate:
        print("\n🤖 STEP 2: Generating content with Groq AI...")
        from scripts.generate_content import generate_all_content
        items = generate_all_content(news, max_items=args.max_items)
    else:
        print("\n🤖 STEP 2: Loading cached generated content...")
        with open("data/generated_content.json", encoding="utf-8") as f:
            items = json.load(f)["items"]
    print(f"   Generated: {len(items)} content packages")

    # ── Step 3: Render videos ────────────────────────────────────
    if not args.skip_render:
        print("\n🎬 STEP 3: Rendering videos with FFmpeg...")
        from scripts.render_video import render_all_videos
        rendered = render_all_videos(items)
    else:
        print("\n🎬 STEP 3: Loading cached rendered video list...")
        with open("data/rendered_videos.json", encoding="utf-8") as f:
            rendered = json.load(f)
    print(f"   Rendered: {len(rendered)} video sets")

    # ── Step 4: Upload OR download ────────────────────────────────
    if args.test:
        print("\n🧪 STEP 4: TEST MODE — listing rendered videos for download:")
        print("-" * 60)
        for item in rendered:
            src = item["content"]["source_item"]
            print(f"\n  📰 {src['source']}: {src['title'][:55]}")
            for style, path in item.get("videos", {}).items():
                p = Path(path)
                if p.exists():
                    size_mb = p.stat().st_size / 1024 / 1024
                    print(f"     [{style}] {p.name}  ({size_mb:.1f} MB)")
        print("\n✅ Download the videos from the GitHub Actions artifacts panel.")
        print("   Go to: Actions → test-run → Artifacts → rendered-videos")
    elif not args.skip_upload:
        print("\n⬆️  STEP 4: Uploading to YouTube...")
        from scripts.upload_youtube import upload_all
        uploaded = upload_all(rendered, max_uploads=args.max_uploads)
        print(f"\n🎉 Done! {len(uploaded)} videos live on YouTube.")
        for v in uploaded:
            print(f"   ▶  {v['youtube_url']}  —  {v['title'][:50]}")
    else:
        print("\n⬆️  STEP 4: Upload skipped (--skip-upload flag)")

    print("\n" + "=" * 60)
    print("  ✅ Pipeline complete!")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simply Reported BD News Auto-Publisher")
    parser.add_argument("--test",          action="store_true", help="Test mode: render but don't upload, save videos as artifacts")
    parser.add_argument("--skip-fetch",    action="store_true", help="Use cached news data")
    parser.add_argument("--skip-generate", action="store_true", help="Use cached generated content")
    parser.add_argument("--skip-render",   action="store_true", help="Use cached rendered videos")
    parser.add_argument("--skip-upload",   action="store_true", help="Don't upload to YouTube")
    parser.add_argument("--max-items",     type=int, default=10, help="Max news items to process")
    parser.add_argument("--max-uploads",   type=int, default=5,  help="Max YouTube uploads per run")
    args = parser.parse_args()
    run_pipeline(args)
