from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, ValidationError
from src.agent.core import ResearchAgent
from src.agent.models import FinalAnswer
from src.utils.config import get_settings
from src.utils.logging import logger
from src.agent.store import JobStore
from typing import Optional, Dict, Any, List
import uuid
import json

# Initialize settings once
settings = get_settings()
store = JobStore()
agent = ResearchAgent(settings=settings, store=store)

app = FastAPI(title="AI Research Agent API")

class ResearchRequest(BaseModel):
    question: str

class JobStatusResponse(BaseModel):
    job_id: str
    question: str
    status: str
    current_stage: str
    logs: List[str] = []
    updated_at: str
    error: Optional[str] = None
    result: Optional[FinalAnswer] = None

def _parse_final_answer(job: Dict[str, Any]) -> tuple[Optional[FinalAnswer], Optional[str]]:
    stored_answer = job.get("final_answer")
    if not stored_answer:
        return None, None

    try:
        answer_data = json.loads(stored_answer) if isinstance(stored_answer, str) else stored_answer
        return FinalAnswer.model_validate(answer_data), None
    except (json.JSONDecodeError, ValidationError) as exc:
        logger.warning(
            "Job {} has a stored report that is incompatible with the current schema: {}",
            job.get("job_id"),
            exc.errors(include_input=False) if isinstance(exc, ValidationError) else str(exc),
        )
        return None, "Stored report is incompatible with the current report schema."

def _job_status_response(job: Dict[str, Any]) -> JobStatusResponse:
    result, result_error = _parse_final_answer(job)
    return JobStatusResponse(
        job_id=job["job_id"],
        question=job["question"],
        status=job["status"],
        current_stage=job["current_stage"],
        logs=job.get("logs", []),
        updated_at=job["updated_at"],
        error=job.get("error") or result_error,
        result=result,
    )

@app.post("/research", response_model=Dict[str, str])
async def submit_research(request: ResearchRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    # Start research in background with 180s startup timeout monitoring
    background_tasks.add_task(agent.run, request.question, job_id=job_id, startup_timeout_seconds=180.0)
    return {"job_id": job_id, "status": "queued"}

@app.get("/job/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return _job_status_response(job)

@app.post("/job/{job_id}/resume", response_model=Dict[str, str])
async def resume_job(job_id: str, background_tasks: BackgroundTasks):
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] == "completed":
        return {"job_id": job_id, "status": "already_completed"}

    # Resume in background
    background_tasks.add_task(agent.run, job["question"], job_id=job_id, resume_from_store=True)
    return {"job_id": job_id, "status": "resuming"}

@app.get("/jobs", response_model=List[JobStatusResponse])
async def list_jobs():
    jobs = store.list_jobs()
    return [_job_status_response(job) for job in jobs]

@app.get("/health")
async def health():
    return {"status": "ok"}
