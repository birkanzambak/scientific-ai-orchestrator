import uuid
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import json
import asyncio
from dotenv import load_dotenv
from .models import AskRequest, AskResponse, TaskResult, TaskStatus, FeedbackRequest, FeedbackResponse
from .workers import run_pipeline, get_task_result

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Scientific AI Orchestrator", 
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=json.loads(os.getenv("CORS_ORIGINS", '["http://localhost:3000"]')),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    """Submit a scientific question for analysis."""
    task_id = str(uuid.uuid4())
    
    # Enqueue the pipeline task
    run_pipeline.delay(request.question, task_id)
    
    return AskResponse(task_id=task_id)

@app.get("/result/{task_id}", response_model=TaskResult)
async def get_result(task_id: str):
    """Get the result of a task."""
    result = get_task_result(task_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return result

@app.get("/stream/{task_id}")
async def stream_progress(task_id: str):
    """Stream progress updates for a task."""
    
    async def event_generator():
        while True:
            result = get_task_result(task_id)
            
            if not result:
                yield {
                    "event": "error",
                    "data": json.dumps({"error": "Task not found"})
                }
                break
            
            # Send current status
            yield {
                "event": "status",
                "data": json.dumps({
                    "status": result.status,
                    "sophia_output": result.sophia_output.dict() if result.sophia_output else None,
                    "nova_output": result.nova_output.dict() if result.nova_output else None,
                    "lyra_output": result.lyra_output.dict() if result.lyra_output else None,
                    "critic_output": result.critic_output.dict() if result.critic_output else None,
                    "error": result.error
                })
            }
            
            # If completed or failed, stop streaming
            if result.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                break
            
            await asyncio.sleep(1)  # Poll every second
    
    return EventSourceResponse(event_generator())

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}

@app.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(feedback: FeedbackRequest):
    """Submit user feedback for a task."""
    try:
        # For now, just log the feedback
        # In production, store in database or Google Form
        print(f"Feedback received for task {feedback.task_id}:")
        print(f"  Rating: {feedback.rating}/5")
        print(f"  Comment: {feedback.comment}")
        print(f"  Email: {feedback.user_email}")
        
        # TODO: Store in database or send to Google Form
        # For Google Form integration, see: https://github.com/your-repo/google-form-feedback
        
        return FeedbackResponse(
            status="submitted",
            message="Thank you for your feedback!"
        )
    except Exception as e:
        return FeedbackResponse(
            status="error",
            message=f"Failed to submit feedback: {str(e)}"
        ) 