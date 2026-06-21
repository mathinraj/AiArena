import asyncio
import json
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sse_starlette.sse import EventSourceResponse

import openai
from google import genai

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GOOGLE_AI_API_KEY = os.getenv("GOOGLE_AI_API_KEY")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.groq_client = openai.AsyncOpenAI(
        api_key=GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1",
    )
    app.state.google_client = genai.Client(api_key=GOOGLE_AI_API_KEY)
    yield


app = FastAPI(title="AIArena", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


async def stream_claude(question: str, queue: asyncio.Queue):
    """Stream Claude response via the CLI (uses existing auth, no API key needed)."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "claude", "-p", question, "--verbose", "--output-format", "stream-json",
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        async for line in proc.stdout:
            text = line.decode("utf-8").strip()
            if not text:
                continue
            try:
                event = json.loads(text)
                if event.get("type") == "assistant":
                    msg = event.get("message", {})
                    content_blocks = msg.get("content", [])
                    for block in content_blocks:
                        if block.get("type") == "text" and block.get("text"):
                            await queue.put({"model": "claude", "type": "chunk", "content": block["text"]})
            except json.JSONDecodeError:
                pass

        await proc.wait()

        if proc.returncode != 0:
            stderr = await proc.stderr.read()
            err_msg = stderr.decode("utf-8").strip()
            if err_msg:
                await queue.put({"model": "claude", "type": "error", "content": err_msg})
    except FileNotFoundError:
        await queue.put({"model": "claude", "type": "error", "content": "Claude CLI not found. Install with: npm install -g @anthropic-ai/claude-code"})
    except Exception as e:
        await queue.put({"model": "claude", "type": "error", "content": str(e)})
    finally:
        await queue.put({"model": "claude", "type": "done"})


async def stream_groq(client: openai.AsyncOpenAI, question: str, queue: asyncio.Queue):
    """Stream Groq (Llama) response via OpenAI-compatible API."""
    try:
        stream = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": question}],
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                await queue.put({"model": "groq", "type": "chunk", "content": delta.content})
    except Exception as e:
        await queue.put({"model": "groq", "type": "error", "content": str(e)})
    finally:
        await queue.put({"model": "groq", "type": "done"})


async def stream_gemini(client: genai.Client, question: str, queue: asyncio.Queue):
    try:
        response = client.models.generate_content_stream(
            model="gemini-2.5-flash",
            contents=question,
        )
        for chunk in response:
            if chunk.text:
                await queue.put({"model": "gemini", "type": "chunk", "content": chunk.text})
    except Exception as e:
        await queue.put({"model": "gemini", "type": "error", "content": str(e)})
    finally:
        await queue.put({"model": "gemini", "type": "done"})


@app.post("/api/ask")
async def ask(request: Request):
    body = await request.json()
    question = body.get("question", "")

    if not question.strip():
        return {"error": "Question cannot be empty"}

    queue = asyncio.Queue()

    async def event_generator():
        tasks = [
            asyncio.create_task(stream_claude(question, queue)),
            asyncio.create_task(stream_groq(request.app.state.groq_client, question, queue)),
            asyncio.create_task(stream_gemini(request.app.state.google_client, question, queue)),
        ]

        done_count = 0
        while done_count < 3:
            event = await queue.get()
            if event["type"] == "done":
                done_count += 1
            yield {"data": json.dumps(event)}

        for task in tasks:
            await task

    return EventSourceResponse(event_generator())


frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/static", StaticFiles(directory=frontend_path), name="static")


@app.get("/")
async def index():
    return FileResponse(os.path.join(frontend_path, "index.html"))
