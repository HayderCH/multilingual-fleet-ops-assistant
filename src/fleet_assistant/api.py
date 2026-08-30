from __future__ import annotations

import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .classifier import classify
from .models import ChatRequest, ChatResponse, ClassifierRequest, ClassifierResponse
from .service import FleetAssistant
from .sessions import MemorySessionStore, RedisSessionStore, SessionStore


def build_store() -> SessionStore:
    ttl = int(os.getenv("SESSION_TTL_SECONDS", "1800"))
    redis_url = os.getenv("REDIS_URL", "").strip()
    return RedisSessionStore(redis_url, ttl) if redis_url else MemorySessionStore(ttl)


STATIC_DIR = Path(__file__).parent / "static"
app = FastAPI(
    title="Multilingual Fleet Operations Assistant",
    version="1.0.0",
    description="Clean-room portfolio API using synthetic fleet data.",
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
assistant = FleetAssistant(build_store())


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "data": "synthetic"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    return await assistant.process(request.text, request.conversation_id)


@app.post("/classify", response_model=ClassifierResponse)
async def classify_intent(request: ClassifierRequest) -> ClassifierResponse:
    return ClassifierResponse(candidates=classify(request.text))


@app.delete("/sessions/{conversation_id}", status_code=204)
async def reset_session(conversation_id: str) -> None:
    await assistant.sessions.delete(conversation_id)


def run() -> None:
    uvicorn.run("fleet_assistant.api:app", host="0.0.0.0", port=8000, reload=False)
