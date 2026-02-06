# AIChairmain

A council of LLMs deliberates on your question. Inspired by [llm-council](https://github.com/karpathy/llm-council), but using direct provider APIs instead of OpenRouter.

## How It Works

**Three-stage deliberation process:**

1. **Responses** — Each council member (GPT-4o, Claude Sonnet, Gemini Flash) independently answers your question.
2. **Peer Review** — Each member reviews and ranks the other responses (anonymized to prevent bias).
3. **Synthesis** — The Chairman model (Claude Opus) synthesizes all responses and reviews into a single definitive answer.

## Architecture

```
backend/          FastAPI server
  providers/      Direct API integrations (OpenAI, Anthropic, Google)
  council.py      3-stage council logic
  storage.py      JSON conversation storage
  config.py       Model & API configuration

frontend/         React + Vite
  src/components/ UI components (query, tabs, reviews, synthesis)
  src/api/        API client
```

## Setup

### 1. Backend

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
python -m backend
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Configuration

Edit `backend/config.py` to change council members or the chairman model. Any model available from OpenAI, Anthropic, or Google can be used.

## Modes

- **Full Council** — Runs all 3 stages automatically and returns the complete result.
- **Step-by-Step** — Runs each stage independently so you can inspect intermediate results.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/council/members` | List council members |
| POST | `/api/council/run` | Run full 3-stage process |
| POST | `/api/council/start` | Start session (Stage 1 only) |
| POST | `/api/council/{id}/review` | Run Stage 2 |
| POST | `/api/council/{id}/synthesize` | Run Stage 3 |
| GET | `/api/council/{id}` | Get session by ID |
| GET | `/api/sessions` | List all sessions |

## License

MIT
