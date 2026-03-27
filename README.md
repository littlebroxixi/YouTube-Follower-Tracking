# YouTube Follower Tracking

Automatically tracks your subscribed YouTube channels daily, fetches video transcripts into `feed.json`, and generates Chinese summaries via Claude Code skill — pushed to Notion automatically.

**[中文文档](README.zh.md)**

---

## Preview

A daily digest is automatically generated in Notion:

```
📺 硅谷101播客 — OpenAI releases o3, how far are we from AGI?
🔗 https://www.youtube.com/watch?v=xxx

💬 Core Takeaway
The host argues o3 has surpassed human expert-level performance on math and coding benchmarks, but still lacks "common sense reasoning" — the key gap before true AGI.

🧭 Background & Premise
- Context: OpenAI released o3 in late 2025, breaking multiple benchmark records
- Stance: Host is cautiously optimistic; benchmarks ≠ real-world capability

📌 Key Arguments
- o3 scored 87.5% on ARC-AGI (human average: 85%) — first to exceed human performance
- Training cost ~$1,000/task; inference cost remains a commercialization bottleneck
- ...

🎯 Conclusion / Recommendation
Watch OpenAI's cost reduction roadmap — 2026 is a critical inflection point

⚠️ Risks & Uncertainties
- Benchmark overfitting risk; actual capability may be overestimated

🔍 Follow-up Threads
- Worth diving into the design philosophy behind ARC-AGI
```

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│               Layer 1: Data Fetching                │
│                                                     │
│  GitHub Actions (runs daily at 15:00 Beijing time)  │
│      ↓                                              │
│  fetch.py                                           │
│      ├── YouTube Data API  →  fetch latest videos   │
│      ├── Supadata API      →  fetch transcripts     │
│      └── write feed.json and push to repo           │
└─────────────────────────────────────────────────────┘
                    ↓ feed.json (publicly accessible)
┌─────────────────────────────────────────────────────┐
│              Layer 2: Summarization                 │
│                                                     │
│  Option A: Manual                                   │
│      Claude Code /YoutuberPointTracking             │
│          └── read feed.json → summarize → save .md  │
│                                                     │
│  Option B: Automated (Claude Code /schedule)        │
│      Remote Agent (runs daily at 15:30)             │
│          └── read feed.json → summarize → Notion    │
└─────────────────────────────────────────────────────┘
```

**Data update logic:**
- Channel has new video today → overwrite that channel's data
- Channel has no new video today → keep previous data, nothing is cleared
- Channel has no historical data → auto-fetch latest video as initial seed

`feed.json` always contains content, even on days when channels don't post.

---

## Tracked Channels (27)

| Channel | Category |
|---------|----------|
| 海伦子 Hellen | US Stocks / Investing |
| 硅谷101播客 | Tech / Startups |
| 美投讲美股 | US Stock Analysis |
| 美股先锋 | US Stock Analysis |
| 美股博士 | US Stock Analysis |
| 老石谈芯 | Chips / Tech |
| 股市咖啡屋 Stock Cafe | US / HK Stocks |
| 视野环球财经 | Macro Finance |
| LEI | Market Analysis |
| PowerUpGammas | Options Strategy |
| Sober 聊期权 CFA | Options / Investing |
| SpaceX | Aerospace |
| 一口新饭 | Finance / Lifestyle |
| 华尔街阿宝 | US Stocks / Finance |
| 富翁電視 MTTV | HK / TW Finance |
| 小Lin说 | Finance Education |
| 小岛大浪吹 | Finance / Current Affairs |
| 投资TALK君 | US Stock Investing |
| BWB - Business With Brian | Business / Investing |
| 猴哥财经 HG Finance | US Stock Finance |
| 美股查理 | US Stock Analysis |
| 美投侃新闻 | Finance News |
| Nick 美股咖啡館 | US Stock Analysis |
| Terry Chen 泰瑞 | US Stocks / Investing |
| Couch Investor | Investing |
| Future Investing | Investing |
| 美股投资网 | US Stock News |

To track additional channels, add entries to the `CHANNELS` list in `fetch.py`:
```python
{"name": "Display Name", "handle": "youtube_handle"},
# Leave handle empty to search by name automatically
```

---

## Setup

### 1. Fork this repository

### 2. Get API Keys

**YouTube Data API v3**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project → Enable YouTube Data API v3
3. Create an API key; set Application restrictions to "None", API restrictions to "YouTube Data API v3"

**Supadata**
1. Sign up at [supadata.ai](https://supadata.ai/)
2. Free tier: 100 transcript fetches per month
3. Copy your API key from the Dashboard

### 3. Add GitHub Secrets

Go to your repo → `Settings → Secrets and variables → Actions → New repository secret`:

| Name | Value |
|------|-------|
| `YOUTUBE_API_KEY` | Your YouTube API Key |
| `SUPADATA_API_KEY` | Your Supadata API Key |

### 4. Enable GitHub Actions

Go to the `Actions` tab and enable Workflows. The job runs daily at UTC 07:00 (15:00 Beijing time). You can also trigger it manually via `Run workflow`.

### 5. Install the Claude Code Skill

```bash
mkdir -p ~/.claude/skills/YoutuberPointTracking
cp SKILL.md ~/.claude/skills/YoutuberPointTracking/SKILL.md
```

Then run `/YoutuberPointTracking` in Claude Code to generate today's summary.

### 6. Set up Notion auto-push (optional)

Use Claude Code's `/schedule` to create a daily remote agent at 15:30 that reads `feed.json` and writes the summary to a Notion page. See `SKILL.md` for the full prompt template.

---

## feed.json Format

```json
{
  "generated_at": "2026-03-28T07:00:00Z",
  "videos": [
    {
      "channel": "硅谷101播客",
      "title": "Video title",
      "url": "https://www.youtube.com/watch?v=xxx",
      "transcript": "Full transcript text (up to 50,000 chars)..."
    }
  ]
}
```

Publicly accessible at:
```
https://raw.githubusercontent.com/<your-username>/YouTube-Follower-Tracking/main/feed.json
```

---

## API Quota

YouTube Data API v3 free daily quota: **10,000 units**

| Operation | API | Cost |
|-----------|-----|------|
| Resolve channel ID by handle | Channels API | 1 unit |
| Fetch latest videos | PlaylistItems API | 1 unit |
| Search channel by name | Search API | 100 units (avoid if possible) |

Normal daily usage for 27 channels: ~**54 units** — well within the free limit.
