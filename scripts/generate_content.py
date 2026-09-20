"""
generate_content.py — Uses Claude to generate Bangla+English scripts,
titles, descriptions, and tags for each news item.
"""

import os
import json
import time
from groq import Groq
from datetime import datetime

client = Groq(api_key=os.environ["GROQ_API_KEY"])

SYSTEM_PROMPT = """You are a professional Bangladeshi news video script writer for "Simply Reported" — 
a popular news Facebook page and YouTube channel. You write in both Bangla and English.

Your style:
- Engaging, clear, journalistic tone
- Mix Bangla and English naturally (like BD news channels do)
- Hook the audience in the first 5 seconds
- Keep scripts 60-90 seconds when read aloud (~150-200 words)
- Use emojis sparingly in titles/descriptions for social media appeal

Always respond with valid JSON only. No extra text."""

def generate_for_item(item: dict) -> dict:
    """Generate full content package for one news item."""
    
    source_type = "YouTube video" if item["type"] == "youtube_video" else "news article"
    
    prompt = f"""Generate a YouTube/Facebook video content package for this {source_type}:

Source: {item['source']}
Title: {item['title']}
Description: {item.get('description', 'N/A')[:300]}
URL: {item.get('video_url', item.get('url', 'N/A'))}

Return a JSON object with exactly these fields:
{{
  "bangla_title": "Catchy Bangla title for YouTube (max 70 chars)",
  "english_title": "Catchy English title for YouTube (max 70 chars)",
  "bangla_script": "Full 150-200 word video script in Bangla",
  "english_script": "Full 150-200 word video script in English",
  "youtube_description_bangla": "SEO YouTube description in Bangla (150 words) with timestamps placeholder",
  "youtube_description_english": "SEO YouTube description in English (150 words)",
  "tags": ["tag1", "tag2", "tag3", "...up to 15 relevant tags in English and Bangla"],
  "facebook_caption_bangla": "Engaging Facebook post caption in Bangla with emojis (max 200 chars)",
  "facebook_caption_english": "Engaging Facebook post caption in English with emojis (max 200 chars)",
  "thumbnail_text": "Short punchy text for thumbnail overlay (max 8 words in Bangla)",
  "category": "News & Politics",
  "hook": "First 5-second hook line in Bangla"
}}"""

    try:
        resp = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            max_tokens=1500,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
            temperature=0.7,
        )
        raw = resp.choices[0].message.content.strip()
        # strip possible markdown fences
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        generated = json.loads(raw)
        generated["source_item"] = item
        return generated
    except Exception as e:
        print(f"  [ERROR] Generation failed for '{item['title'][:50]}': {e}")
        return None


def generate_all_content(news_data: dict, max_items: int = 10) -> list[dict]:
    """Generate content for the top N most recent news items."""
    all_items = news_data["videos"] + news_data["articles"]
    # prioritise YouTube videos first, then articles
    all_items.sort(key=lambda x: (x["type"] != "youtube_video", x.get("published_at", "")))
    
    selected = all_items[:max_items]
    results  = []

    print(f"\n🤖 Generating content for {len(selected)} news items...")
    for i, item in enumerate(selected, 1):
        print(f"  [{i}/{len(selected)}] {item['source']}: {item['title'][:60]}...")
        content = generate_for_item(item)
        if content:
            results.append(content)
        time.sleep(1)  # avoid rate limits

    output = {
        "generated_at": datetime.utcnow().isoformat(),
        "count": len(results),
        "items": results,
    }

    with open("data/generated_content.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Generated content for {len(results)} items")
    return results


if __name__ == "__main__":
    with open("data/news_raw.json", encoding="utf-8") as f:
        news_data = json.load(f)
    generate_all_content(news_data)
