# MeteoAgent

Agent-powered weather assistant with FastAPI backend and React (Vite) frontend. The backend fetches weather from OpenWeather and can leverage an LLM via OpenRouter; the frontend provides a fast, modern UI.

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

## Local Development

### Backend (FastAPI)

1. Create a virtual environment and install deps:

```
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

2. Configure environment:

Copy `backend/.env.example` to `backend/.env` and fill values.

```
OPENROUTER_API_KEY=...
OPENROUTER_MODEL=openai/gpt-4o-mini
WEATHER_API_KEY=...
```

3. Run the API locally:

```
uvicorn app.main:app --reload
```

The API defaults to `http://127.0.0.1:8000`.

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

The app reads the backend base URL from `VITE_BACKEND_URL` and calls `/chat`, `/weather`, and `/weather/batch`.

## Deployment

### Backend → Render (Free)

- File: `render.yaml` at repo root
- Service name: `meteo-agent-backend`
- Root dir: `backend`
- Build: `pip install -r requirements.txt`
- Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

Steps (Render Dashboard):

- New Web Service → "Build & deploy from a Git repo"
- Root Directory: `backend`
- Auto-detected from `render.yaml` or configure manually.

Required env vars (Render → Environment):

- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL` (default `openai/gpt-4o-mini`)
- `WEATHER_API_KEY`

### Frontend → Vercel (Static)

- File: `vercel.json` at repo root
- Build uses `@vercel/static-build` targeting `weather-app/package.json`

Steps (Vercel Dashboard):

- Import Git repository
- Set Root Directory to `frontend` or repo root as per your setup
- If using repo root, `vercel.json` routes to `weather-app/dist`
- Add env: `VITE_BACKEND_URL` pointing to your Render backend URL

## API Endpoints

- `POST /chat` → `{ message: string }` → AI/logic response
- `GET /weather?city=CityName` → structured current weather
- `POST /weather/batch` → `{ cities: string[] }` → array of weather objects

## Technologies

- Backend: FastAPI, Uvicorn, Requests, LangChain, LangChain OpenAI, python-dotenv
- Frontend: React, Vite

## Notes

- CORS is enabled with permissive defaults (`*`) for production compatibility. Set explicit origins if needed.
- Keep secrets in `.env` files locally and provider env in deployment.
