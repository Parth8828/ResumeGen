
from fastapi import APIRouter
from app.services.job_service import job_service
from app.schemas.schemas import JobSearchRequest
from typing import List, Dict

router = APIRouter()

@router.post("/search", response_model=List[Dict])
async def search_jobs(request: JobSearchRequest):
    """
    Searches for jobs using the configured Job Service (Arbeitnow + Fallback).
    """
    return job_service.search_jobs(request.query, request.location)
