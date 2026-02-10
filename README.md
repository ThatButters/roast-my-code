# Roast My Code

<!-- Badges -->
![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Docker](https://img.shields.io/badge/docker-ready-blue)

**Paste your puny human-written code. An AI will tell you what you did wrong.**

Roast My Code is an AI-powered code review tool with two modes:

- **Roast Mode** — Claude tears apart your code with entertaining commentary, points out real issues, and shows how AI-assisted coding (Claude Code) would have caught them. If your code is actually good, it earns genuine praise.
- **Serious Mode** — Drops the humor for a legitimate senior-dev-level code review with actionable feedback.

The hook: funny roasts that get shared. The credibility play: good code gets recognized honestly.

<!-- Screenshot placeholder -->
*Screenshot coming soon*

## Features

- **Roast Score** (0-100) — Dramatic visual gauge showing how badly your code needs help
- **Flavor Rotation** — 12+ comedy styles keep roasts fresh and shareable
- **4 Severity Levels** — Gentle, Normal, Brutal, Unhinged
- **Shareable URLs** — Every roast gets a unique link with Open Graph tags
- **Language Detection** — Auto-detects 17+ languages via pattern matching
- **Budget Controls** — Monthly spend tracking, daily rate limits, admin kill switch
- **Admin Panel** — Real-time dashboard with spend velocity, config editor, usage logs

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Flask (Python 3.12) |
| Frontend | Jinja2 templates, vanilla JS |
| Database | SQLite (WAL mode) |
| AI | Claude API (Haiku 4.5 default) |
| Server | Gunicorn |
| Deployment | Docker |

## Quick Start

### Docker (Recommended)

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/roast-my-code.git
cd roast-my-code

# Set up environment
cp .env.example .env
# Edit .env with your values:
#   ANTHROPIC_API_KEY=sk-ant-...
#   ADMIN_PASSWORD=your-secure-password
#   SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")

# Run
docker compose up -d

# Visit http://localhost:5001
```

### Without API Key (Mock Mode)

The app works without an `ANTHROPIC_API_KEY` — it returns mock roasts for testing the full flow locally without burning API credits.

## Self-Hosting

Designed to run as a Docker container on a VPS behind a reverse proxy.

```yaml
# docker-compose.yml binds to localhost only
ports:
  - "127.0.0.1:5001:5000"
```

### Reverse Proxy (Nginx example)

```nginx
server {
    server_name roastmycode.dev;

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | No* | Claude API key from console.anthropic.com |
| `ADMIN_PASSWORD` | Yes | Password for `/admin` panel |
| `SECRET_KEY` | Yes | Flask session signing key |
| `DATABASE_URL` | No | SQLite path (default: `sqlite:///data/roasts.db`) |

*Without an API key, the app runs in mock mode with sample responses.

### Budget Safety

Set a hard spending limit in the [Anthropic Console](https://console.anthropic.com):
- Console > Settings > Billing > Monthly Spend Limit > $25
- This is your backstop even if app-level budget tracking has a bug

## Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Run locally
python -m app.main
# Visit http://localhost:5000
```

### Running Tests

```bash
pytest tests/ -v
```

### Project Structure

```
roastmycode/
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── requirements.txt
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── main.py              # Routes
│   ├── roaster.py           # Claude API + prompts + flavor rotation
│   ├── budget.py            # Monthly budget tracking
│   ├── config.py            # App config interface
│   ├── rate_limit.py        # Session → IP → global rate limiting
│   ├── db.py                # SQLite init + schema
│   ├── language_detect.py   # Pattern-based language detection
│   ├── security.py          # Input validation + sanitization
│   ├── templates/           # Jinja2 templates
│   └── static/              # CSS + JS
└── tests/
```

## Rate Limiting

Uses layered identity — not pure IP-based:

| Layer | Limit | Purpose |
|-------|-------|---------|
| Session cookie | 10/day | Primary per-user limit |
| IP ceiling | 30/day | Anti-abuse (invisible to normal users) |
| Global cap | 500/day | Infrastructure safety net |
| Monthly budget | $20/month | Hard cost stop |

## Roadmap

- [x] **Phase 1: MVP Web App** — Paste code, get a shareable roast
- [ ] **Phase 2: Polish & CLI** — Streaming responses, `pip install roastmycode`
- [ ] **Phase 3: API** — `POST /api/v1/roast` with API keys
- [ ] **Phase 4: Discord Bot** — `/roast` command in servers
- [ ] **Phase 5: Nice-to-Haves** — Leaderboard, OG images, GitHub PR integration

## License

MIT
