# MeteoAgent

Intelligent, agent-powered weather assistant with FastAPI + React. It fetches real-time weather from OpenWeather, reasons using LangChain + OpenRouter, and presents clean insights in a modern UI.

**Live App:** https://meteo-agent.vercel.app/

**Video Demo:** https://drive.google.com/file/d/1aqayRaEkO423m6DVW3O4L9MFkC9fKbb8/view?usp=sharing

## Highlights

- **AI Assistant:** Intent detection, multi-city comparison, and concise forecast summaries (weekend, tomorrow, hourly).
- **Production-Ready:** Env-driven config, CORS enabled, clean deploy configs for Render (backend) and Vercel (frontend).
- **Clear API Surface:** Simple, composable endpoints for chat and weather data.
- **Modern Frontend:** Vite + React with responsive components and smooth UX.

## Architecture

- **Frontend (Vite + React):** SPA served on Vercel. Reads backend base URL from `VITE_BACKEND_URL`.
- **Backend (FastAPI):** REST API hosted on Render. Serves:
  - `POST /chat` — routes to tools/LLM based on intent
  - `GET /weather?city=...` — structured current weather
  - `POST /weather/batch` — best-effort multi-city weather
- **Data & LLM:** OpenWeather for data; OpenRouter for LLM access via LangChain.
- **CORS:** Permissive defaults for cross-origin frontends (can be tightened per deployment).

## Tech Stack

- **Backend:** FastAPI, Uvicorn, Requests, Pydantic v2, LangChain, LangChain OpenAI, python-dotenv
- **Frontend:** React, Vite
- **Hosting:** Render (backend), Vercel (frontend)

## Project Structure

```
MeteoAgent/
	backend/
		app/
			main.py
			agent.py
			tools.py
			schemas.py
			intent.py
			prompts.py
		requirements.txt
		.env.example
	frontend/
		weather-app/
			src/
			package.json
			vite.config.js
			.env.example
	render.yaml
	vercel.json
	README.md
	.gitignore
```

## Getting Started (Local)

### Backend (FastAPI)

1. Create a virtual environment and install deps:

```
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

2. Configure environment:

Copy `backend/.env.example` to `backend/.env` and fill values (store secrets outside git):

```
OPENROUTER_API_KEY=...
OPENROUTER_MODEL=openai/gpt-4o-mini
WEATHER_API_KEY=...
```

3. Run the API locally:

```
uvicorn app.main:app --reload
```

### Frontend (Vite + React)

1. Install dependencies:

```
cd frontend/weather-app
npm install
```

2. Set backend URL via env:

Copy `.env.example` to `.env` and set:

```
VITE_BACKEND_URL=http://127.0.0.1:8000
```

3. Run the dev server:

```
npm run dev
```

## Environment Variables

- **Backend:**
  - `OPENROUTER_API_KEY` — OpenRouter API key
  - `OPENROUTER_MODEL` — defaults to `openai/gpt-4o-mini`
  - `WEATHER_API_KEY` — OpenWeather API key
- **Frontend:**
  - `VITE_BACKEND_URL` — base URL of deployed backend

## Deployment

### Backend → Render (Free)

- File: `render.yaml` at repo root
- Root dir: `backend`
- Build: `pip install -r requirements.txt`
- Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

Steps (Render Dashboard):

- New Web Service → "Build & deploy from a Git repo"
- Root Directory: `backend`
- Auto-detected from `render.yaml` or configure manually.

Required env vars:

- `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, `WEATHER_API_KEY`

### Frontend → Vercel (Static)

- File: `vercel.json` at repo root
- Build uses `@vercel/static-build` targeting `weather-app/package.json`
- Set `VITE_BACKEND_URL` to your Render backend URL

## API Reference

- `POST /chat` → `{ message: string }` → AI/logic response
- `GET /weather?city=CityName` → structured current weather
- `POST /weather/batch` → `{ cities: string[] }` → array of weather objects

## What I Built

- Designed a clean, deployable full-stack app with clear separation of concerns.
- Implemented intent detection and weather tools with robust error handling.
- Wired environment-driven configs for portability across local/dev/prod.
- Added Render/Vercel configs for one-click deployments.

## Notes

- CORS uses permissive defaults for compatibility; tighten as needed per environment.
- Secrets live in provider env or local `.env` only; `.gitignore` prevents accidental commits.
