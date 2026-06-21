# AIArena

Ask once, compare many. A lightweight web app that sends your question to multiple LLMs in parallel and streams all responses side by side.

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API keys

Copy the example env file and add your keys:

```bash
cp .env.example .env
```

Edit `.env` with your actual keys:

- **GROQ_API_KEY** — Get from https://console.groq.com/
- **GOOGLE_AI_API_KEY** — Get from https://aistudio.google.com/apikey (free tier available)

### 3. Run

```bash
uvicorn backend.main:app --reload --port 8000
```

Open http://localhost:8000 in your browser.

## Usage

Type a question and press **Ask All Models** (or `Cmd+Enter` / `Ctrl+Enter`). All models respond simultaneously with streamed output.

## Project Structure

```
aiarena/
├── backend/
│   └── main.py          # FastAPI server with parallel streaming
├── frontend/
│   ├── index.html       # Single-page UI
│   ├── style.css        # Dark theme styling
│   └── app.js           # SSE client logic
├── .env.example         # API key template
├── requirements.txt     # Python dependencies
└── README.md
```
