"""
AIChairmain — FastAPI application.
A council of LLMs that deliberate on your question.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.config import FRONTEND_URL, COUNCIL_MEMBERS, CHAIRMAN_MODEL
from backend.models import QueryRequest, CouncilSession
from backend.council import (
    run_full_council,
    run_stage_responses,
    run_stage_review,
    run_stage_synthesis,
)
from backend.storage import load_session, list_sessions, save_session

import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("AIChairmain starting up")
    logger.info(f"Council members: {[m['name'] for m in COUNCIL_MEMBERS]}")
    logger.info(f"Chairman: {CHAIRMAN_MODEL['name']}")
    yield
    logger.info("AIChairmain shutting down")


app = FastAPI(
    title="AIChairmain",
    description="A council of LLMs deliberates on your question",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Endpoints ──────────────────────────────────────────────────────────────


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/council/members")
async def get_members():
    """Return the configured council members and chairman."""
    return {
        "members": COUNCIL_MEMBERS,
        "chairman": CHAIRMAN_MODEL,
    }


@app.post("/api/council/run")
async def run_council(req: QueryRequest):
    """Run the full 3-stage council process and return results."""
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    session = await run_full_council(req.query.strip())
    return session.model_dump()


@app.post("/api/council/start")
async def start_session(req: QueryRequest):
    """Create a session and run Stage 1 (gather responses)."""
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    session = CouncilSession(
        session_id=str(uuid.uuid4()),
        query=req.query.strip(),
        stage="responses",
    )
    save_session(session)
    session = await run_stage_responses(session)
    return session.model_dump()


@app.post("/api/council/{session_id}/review")
async def review_session(session_id: str):
    """Run Stage 2 (peer review) for an existing session."""
    session = load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.stage != "review":
        raise HTTPException(status_code=400, detail=f"Session is in stage '{session.stage}', expected 'review'")

    session = await run_stage_review(session)
    return session.model_dump()


@app.post("/api/council/{session_id}/synthesize")
async def synthesize_session(session_id: str):
    """Run Stage 3 (chairman synthesis) for an existing session."""
    session = load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.stage != "synthesis":
        raise HTTPException(status_code=400, detail=f"Session is in stage '{session.stage}', expected 'synthesis'")

    session = await run_stage_synthesis(session)
    return session.model_dump()


@app.get("/api/council/{session_id}")
async def get_session(session_id: str):
    """Retrieve a session by ID."""
    session = load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.model_dump()


@app.get("/api/sessions")
async def get_sessions():
    """List all saved sessions."""
    return list_sessions()
