# 🇧🇩 Simply Reported — BD News Auto-Publisher

A fully automated pipeline that fetches news from **every major Bangladeshi news source**, generates bilingual (Bangla + English) video scripts using **Claude AI**, renders videos with **FFmpeg**, and uploads them to **YouTube** — all running free on **GitHub Actions**.

---

## 🗂️ Project Structure

```
youtube-autopilot/
├── .github/workflows/
│   └── daily_publish.yml      ← GitHub Actions (runs twice daily, free)
├── scripts/
│   ├── fetch_news.py          ← Pulls from 11 YouTube channels + 12 RSS feeds
│   ├── generate_content.py    ← Claude AI generates scripts, titles, tags
│   ├── render_video.py        ← FFmpeg renders 3 video styles
│   ├── upload_youtube.py      ← YouTube Data API v3 uploader
│   └── main.py                ← Pipeline orchestrator
├── setup_oauth.py             ← Run ONCE locally to get YouTube credentials
├── requirements.txt
└── README.md
```

---

## 📡 BD News Sources Covered

### YouTube Channels (videos pulled directly)
| Channel | Subscribers |
|---|---|
| Jamuna TV | 30.7M |
| Channel 24 | 16.8M |
| Somoy TV | ~15M |
| Ekattor TV | 15.8M |
| NTV | ~12M |
| RTV News | 10.9M |
| Independent TV | 12.3M |
| ATN News | 10.1M |
| DBC News | ~5M |
| Banglavision News | ~4M |
| News24 Bangladesh | ~3M |

### Online News Portals (RSS feeds)
Prothom Alo · Daily Star · bdnews24 · Janobani · Jugantor · Kaler Kantho · Samakal · Manabzamin · Ittefaq · Bangladesh Pratidin · Dhaka Tribune · New Age BD

---

## 🎬 Video Styles

| Style | Description |
|---|---|
| **Text on Background** | Dark cinematic background with animated Bangla text — fast to render |
| **Slideshow** | Original news thumbnail as background + text overlay — looks professional |
| **Audio + Subtitles** | gTTS Bangla voice + burned-in subtitles — great for mobile |

---

## ⚙️ Setup (One-Time)

### Step 1 — Fork & clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/simply-reported-autopilot
cd simply-reported-autopilot
```

### Step 2 — Get API keys

#### A) YouTube Data API v3 key
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project → Enable **YouTube Data API v3**
3. Go to **Credentials** → **Create Credentials** → **API Key**
4. Copy the key

#### B) YouTube OAuth2 credentials (for uploading)
1. In the same project → **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
2. Application type: **Desktop app**
3. Download the `client_secret.json`
4. On your PC, run:
   ```bash
   pip install google-auth-oauthlib
   python setup_oauth.py --client-secrets client_secret.json
   ```
5. A browser opens → sign in with the YouTube channel owner's Google account
6. Copy the JSON output

#### C) Groq API key (free)
1. Go to [console.groq.com](https://console.groq.com)
2. Sign up (free) → **API Keys** → **Create API Key**
3. Copy the key — it's completely free with generous daily limits

### Step 3 — Add GitHub Secrets
Go to your repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

| Secret Name | Value |
|---|---|
| `YOUTUBE_API_KEY` | Your YouTube Data API v3 key |
| `GROQ_API_KEY` | Your Groq API key (free at console.groq.com) |
| `YOUTUBE_OAUTH_CREDENTIALS` | The full JSON from setup_oauth.py |

### Step 4 — Push to GitHub
```bash
git add .
git commit -m "🚀 Initial setup"
git push
```

The workflow runs automatically at **6:00 AM** and **12:00 PM** Bangladesh time every day.

---

## 🕹️ Manual Run

Go to your repo → **Actions** → **🇧🇩 Simply Reported — Daily BD News Publisher** → **Run workflow**

Options:
- `max_items` — how many news stories to process (default: 10)
- `max_uploads` — how many videos to upload (default: 5)
- `skip_upload` — dry run, render but don't upload (default: false)

---

## 💸 Cost Estimate

| Service | Cost |
|---|---|
| GitHub Actions | **Free** (2,000 min/month on free plan) |
| YouTube Data API | **Free** (10,000 units/day quota) |
| Groq API | **Free** (llama-3.3-70b-versatile, generous daily limit) |
| FFmpeg rendering | **Free** (runs on GitHub's servers) |

**Total: 100% free.** GitHub Actions + YouTube API + Groq are all free tiers.

---

## 📝 Notes

- Videos are uploaded as **public** by default. Change `privacyStatus` in `upload_youtube.py` to `"unlisted"` or `"private"` if you want to review first.
- The pipeline respects YouTube's upload quota. By default it uploads max 5 videos per run.
- Thumbnail images are downloaded from original news sources and used as slideshow backgrounds.
- All scripts and titles are generated in **Bangla first**, English second.
