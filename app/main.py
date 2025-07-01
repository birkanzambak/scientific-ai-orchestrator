# main.py  – API gateway for Scientific AI Orchestrator
import uuid, os, json, asyncio
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

import redis                               # ← NEW
from .models import (
    AskRequest, AskResponse,
    TaskResult, TaskStatus,
    FeedbackRequest, FeedbackResponse
)
from .workers import run_pipeline          # get_task_result is no longer imported

# ─────────────────────────  bootstrap  ──────────────────────────
load_dotenv()

app = FastAPI(
    title="Scientific AI Orchestrator",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=json.loads(os.getenv("CORS_ORIGINS", '["http://localhost:3000"]')),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ───────────────────────  shared Redis  client  ─────────────────
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
r = redis.from_url(REDIS_URL, decode_responses=True)

RESULT_KEY = "result:{}"   # helper for namespacing


# ──────────────────────────  endpoints  ─────────────────────────
@app.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    """Submit a scientific question for analysis and get back a task-id."""
    task_id = str(uuid.uuid4())
    # enqueue celery job
    run_pipeline.delay(request.question, task_id)
    return AskResponse(task_id=task_id)


@app.get("/result/{task_id}", response_model=TaskResult)
async def get_result(task_id: str):
    """Return the stored JSON for a finished task, or 404 until it exists."""
    blob = r.get(RESULT_KEY.format(task_id))
    if not blob:
        raise HTTPException(status_code=404, detail="Task not found")
    return json.loads(blob)


@app.get("/stream/{task_id}")
async def stream_progress(task_id: str):
    """Server-sent-events stream that polls redis every second."""
    async def event_generator():
        while True:
            blob = r.get(RESULT_KEY.format(task_id))
            if not blob:                        # not ready yet
                yield {"event": "status", "data": json.dumps({"status": "processing"})}
            else:                               # finished → send once & exit
                data = json.loads(blob)
                yield {"event": "status", "data": json.dumps(data)}
                break
            await asyncio.sleep(1)

    return EventSourceResponse(event_generator())


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}


@app.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(feedback: FeedbackRequest):
    try:
        print("Feedback:", feedback.json(indent=2))
        return FeedbackResponse(status="submitted",
                                message="Thank you for your feedback!")
    except Exception as exc:
        return FeedbackResponse(status="error", message=str(exc))
