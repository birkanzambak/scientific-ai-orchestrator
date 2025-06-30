import os
import asyncio
from celery import Celery
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from .models import TaskResult, TaskStatus
from ..agents.sophia import Sophia
from ..agents.nova import Nova
from ..agents.lyra import Lyra
from ..agents.critic import Critic

# Celery app configuration
celery_app = Celery(
    "orchestrator",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0")
)

# In-memory storage for demo (use Redis/DB in production)
task_results = {}

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((Exception,))
)
def run_with_timeout(func, *args, timeout=30, **kwargs):
    """Run a function with timeout and retry logic."""
    try:
        # For async functions, we need to handle differently
        if asyncio.iscoroutinefunction(func):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(asyncio.wait_for(func(*args, **kwargs), timeout=timeout))
            finally:
                loop.close()
        else:
            return func(*args, **kwargs)
    except Exception as e:
        print(f"Error in {func.__name__}: {e}")
        raise

@celery_app.task(bind=True)
def run_pipeline(self, question: str, task_id: str):
    """Run the complete scientific analysis pipeline."""
    
    try:
        # Initialize task result
        task_results[task_id] = TaskResult(
            task_id=task_id,
            status=TaskStatus.PROCESSING,
            question=question
        )
        
        # Step 1: Sophia - Question Classification
        self.update_state(state="PROGRESS", meta={"step": "sophia"})
        sophia = Sophia()
        sophia_output = run_with_timeout(sophia.run, question, timeout=30)
        task_results[task_id].sophia_output = sophia_output
        
        # Step 2: Nova - Evidence Retrieval
        self.update_state(state="PROGRESS", meta={"step": "nova"})
        nova = Nova()
        nova_output = run_with_timeout(nova.run, sophia_output, timeout=30)
        task_results[task_id].nova_output = nova_output
        
        # Step 3: Lyra - Reasoning
        self.update_state(state="PROGRESS", meta={"step": "lyra"})
        lyra = Lyra()
        lyra_output = run_with_timeout(lyra.run, question, nova_output, timeout=60)
        task_results[task_id].lyra_output = lyra_output
        
        # Step 4: Critic - Verification (optional)
        self.update_state(state="PROGRESS", meta={"step": "critic"})
        critic = Critic()
        critic_output = run_with_timeout(critic.run, question, lyra_output, timeout=30)
        task_results[task_id].critic_output = critic_output
        
        # Step 5: Rerun Lyra if critic fails
        if not critic_output.passes:
            self.update_state(state="PROGRESS", meta={"step": "lyra_rerun"})
            lyra_output = run_with_timeout(lyra.run, question, nova_output, critique=critic_output.dict(), timeout=60)
            task_results[task_id].lyra_output = lyra_output
        
        # Mark as completed
        task_results[task_id].status = TaskStatus.COMPLETED
        
        return {
            "status": "completed",
            "task_id": task_id,
            "result": task_results[task_id].dict()
        }
        
    except Exception as e:
        task_results[task_id].status = TaskStatus.FAILED
        task_results[task_id].error = str(e)
        
        return {
            "status": "failed",
            "task_id": task_id,
            "error": str(e)
        }

def get_task_result(task_id: str) -> TaskResult:
    """Get task result from storage."""
    return task_results.get(task_id) 