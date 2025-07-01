"""
workers.py – Celery worker for Scientific AI Orchestrator
---------------------------------------------------------

Runs the Sophia → Nova → Lyra → Critic pipeline and writes the final JSON
to Redis so the API container can fetch it.
"""

from __future__ import annotations

import os
import json
import asyncio
from datetime import timedelta
from typing import Any, Callable

import redis
from celery import Celery
from tenacity import (
    retry, stop_after_attempt, wait_exponential, retry_if_exception_type
)

from .models import TaskResult, TaskStatus
from agents.sophia import Sophia
from agents.nova import Nova
from agents.lyra import Lyra
from agents.critic import Critic

# ─────────────────────────── Redis client ────────────────────────────
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client: redis.Redis = redis.from_url(REDIS_URL, decode_responses=True)
RESULT_KEY = "result:{}"          # namespaced key
RESULT_TTL = timedelta(days=1).total_seconds()

# ─────────────────────────── Celery config ───────────────────────────
celery_app = Celery(
    "orchestrator",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

# optional: mute the CPendingDeprecationWarning in Celery 6
celery_app.conf.broker_connection_retry_on_startup = True

# ───────────────────────── helper: timeout+retry ─────────────────────
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(Exception),
)
def run_with_timeout(
    func: Callable[..., Any],
    *args,
    timeout: int = 30,
    **kwargs,
):
    """Run a sync **or** async function with timeout + retry."""
    try:
        if asyncio.iscoroutinefunction(func):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                coro = func(*args, **kwargs)
                return loop.run_until_complete(asyncio.wait_for(coro, timeout))
            finally:
                loop.close()
        else:
            return func(*args, **kwargs)
    except Exception as exc:
        print(f"[run_with_timeout] {func.__name__} failed → {exc}")
        raise


# ────────────────────────────  Celery task  ──────────────────────────
@celery_app.task(bind=True, name="run_pipeline")
def run_pipeline(self, question: str, task_id: str):
    """
    Execute the full pipeline and persist the JSON result in Redis.

    Returns a light dict so Celery’s result backend is small; the full
    payload is stored under result:{task_id}.
    """

    # Local copy for incremental status tracking / debugging
    task_results: dict[str, TaskResult] = {
        task_id: TaskResult(
            task_id=task_id, status=TaskStatus.PROCESSING, question=question
        )
    }

    try:
        # 1️⃣ Sophia
        self.update_state(state="PROGRESS", meta={"step": "sophia"})
        sophia_out = run_with_timeout(Sophia().run, question, timeout=30)
        task_results[task_id].sophia_output = sophia_out

        # 2️⃣ Nova
        self.update_state(state="PROGRESS", meta={"step": "nova"})
        nova_out = run_with_timeout(Nova().run, sophia_out, timeout=30)
        task_results[task_id].nova_output = nova_out

        # 3️⃣ Lyra
        self.update_state(state="PROGRESS", meta={"step": "lyra"})
        lyra_inst = Lyra()
        lyra_out = run_with_timeout(
            lyra_inst.run, question, nova_out, timeout=60
        )
        task_results[task_id].lyra_output = lyra_out

        # 4️⃣ Critic
        self.update_state(state="PROGRESS", meta={"step": "critic"})
        critic_out = run_with_timeout(
            Critic().run, question, lyra_out, timeout=30
        )
        task_results[task_id].critic_output = critic_out

        # 5️⃣ Optional Lyra rerun if Critic fails
        if not critic_out.passes:
            self.update_state(state="PROGRESS", meta={"step": "lyra_rerun"})
            lyra_out = run_with_timeout(
                lyra_inst.run,
                question,
                nova_out,
                critique=critic_out.dict(),
                timeout=60,
            )
            task_results[task_id].lyra_output = lyra_out

        # ✅ Completed
        task_results[task_id].status = TaskStatus.COMPLETED

    except Exception as exc:
        task_results[task_id].status = TaskStatus.FAILED
        task_results[task_id].error = str(exc)
        print(f"[run_pipeline] task {task_id} failed → {exc}")

    # ─── persist to Redis ────────────────────────────────────────────
    final_json = task_results[task_id].dict()
    redis_client.setex(
        RESULT_KEY.format(task_id), int(RESULT_TTL), json.dumps(final_json)
    )

    # Return a lightweight status for Celery result backend
    return {
        "status": final_json["status"],
        "task_id": task_id,
    }
