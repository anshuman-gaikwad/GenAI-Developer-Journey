
"""
GrahakNyay FastAPI service.

Run:
    python -m uvicorn app.main:app --reload

Docs:
    http://127.0.0.1:8000/docs
"""

import json
import logging
import re
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.graph import run_agent_graph
from app.llm import generate_response
from app.rag import answer_question
from app.response_cache import (
    get_cached_response,
    is_cacheable_question,
    normalize_question,
    set_cached_response,
)
from app.smart_search import RECORDS, rank_records
from app.vectorstore import semantic_search

# Configure application logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="GrahakNyay API",
    description=(
        "General consumer-rights information from Indian consumer law. "
        "Not legal advice."
    ),
    version="0.1.0",
)

DISCLAIMER = (
    "This is general consumer-rights information, not legal advice. "
    "Please verify current rules and fees on official government sources."
)


# ---------------------------------------------------------------
# Day 13: API request latency logging
# ---------------------------------------------------------------


@app.middleware("http")
async def log_request_latency(request: Request, call_next):
    """Log request duration and HTTP status without logging user questions."""

    start_time = time.perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
        return response

    finally:
        latency_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            "api_request method=%s path=%s status=%s latency_ms=%.2f",
            request.method,
            request.url.path,
            status_code,
            latency_ms,
        )


# Project folders
BASE_DIR = Path(__file__).resolve().parent.parent
PROMPTS_DIR = BASE_DIR / "prompts"


# ---------------------------------------------------------------
# Request models
# ---------------------------------------------------------------


class Question(BaseModel):
    question: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="The consumer's problem or question (3–2000 characters)",
    )

    name: str | None = Field(default=None, description="Consumer's name (optional)")



class ChatQuestion(BaseModel):
    question: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="Ask a consumer-rights question (3–2000 characters)",
    )



# ---------------------------------------------------------------
# Helper: Check case-decision timeline questions
# ---------------------------------------------------------------


def is_timeline_question(question):
    question = question.lower()

    asks_duration = bool(
        re.search(
            r"\b(how long|how much time|time taken|"
            r"expected time|duration|take to decide)\b",
            question,
        )
    )

    mentions_case = bool(
        re.search(r"\b(case|commission|complaint|decision|decide)\b", question)
    )

    return asks_duration and mentions_case


# ---------------------------------------------------------------
# Helper: Read prompt files
# ---------------------------------------------------------------


def read_prompt(filename):
    prompt_path = PROMPTS_DIR / filename

    if not prompt_path.exists():
        raise HTTPException(
            status_code=500, detail=f"Prompt file not found: {filename}"
        )

    return prompt_path.read_text(encoding="utf-8")


# ---------------------------------------------------------------
# Helper: Parse the LLM JSON response
# ---------------------------------------------------------------


def parse_chat_response(response_text):
    """
    Convert the LLM response into the required JSON fields.
    """

    cleaned_text = response_text.strip()

    # Remove Markdown code fences if the model adds them.
    if cleaned_text.startswith("```"):
        cleaned_text = re.sub(
            r"^```(?:json)?\s*", "", cleaned_text, flags=re.IGNORECASE
        )
        cleaned_text = re.sub(r"\s*```$", "", cleaned_text)

    try:
        result = json.loads(cleaned_text)

        answer = result.get("answer")
        confidence = result.get("confidence")
        follow_up = result.get("follow_up")

        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
            raise TypeError("The answer field must be text.")

        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
            raise TypeError("Confidence must be a number.")

        confidence = float(confidence)

        if not 0.0 <= confidence <= 1.0:
            raise ValueError("Confidence must be between 0 and 1.")

        if follow_up is not None and not isinstance(follow_up, str):
            raise ValueError("Follow-up must be text or null.")

        return {"answer": answer, "confidence": confidence, "follow_up": follow_up}

    except (json.JSONDecodeError, ValueError, TypeError, AttributeError):
        raise HTTPException(
            status_code=502,
            detail=("The AI provider returned an invalid response. Please try again."),
        )


# ---------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------


@app.get("/health")
def health():
    """Check that the service is running."""
    return {"status": "ok", "records_loaded": len(RECORDS)}


# ---------------------------------------------------------------
# GET /records?limit=
# ---------------------------------------------------------------


@app.get("/records")
def list_records(
    limit: int = Query(
        default=10, ge=1, le=100, description="How many records to return"
    ),
):
    """Return the first 'limit' records."""
    return {
        "total": len(RECORDS),
        "returned": len(RECORDS[:limit]),
        "records": RECORDS[:limit],
    }


# ---------------------------------------------------------------
# GET /records/{record_id}
# ---------------------------------------------------------------


@app.get("/records/{record_id}")
def get_record(record_id: int):
    """Return one record by ID. Return 404 if it does not exist."""
    for record in RECORDS:
        if record["id"] == record_id:
            return record

    raise HTTPException(status_code=404, detail=f"Record {record_id} not found")


# ---------------------------------------------------------------
# GET /search?q=
# ---------------------------------------------------------------


@app.get("/search")
def search(
    q: str = Query(..., min_length=1, description="Words to search for"),
    top_k: int = Query(default=5, ge=1, le=20, description="Maximum results"),
):
    """Search records using TF-IDF and cosine similarity."""
    results = rank_records(q, top_k=top_k)

    return {"query": q, "count": len(results), "results": results}


# ---------------------------------------------------------------
# POST /questions
# ---------------------------------------------------------------


@app.post("/questions")
def ask_question(body: Question):
    """Return relevant legal provisions for a consumer question."""

    if is_timeline_question(body.question):
        return {
            "name": body.name,
            "question": body.question,
            "answer": (
                "Sorry, the current GrahakNyay data does not contain "
                "reliable information about the expected decision time "
                "for a specific consumer case. Please contact the "
                "relevant Consumer Commission."
            ),
            "answerable": False,
            "matches": [],
            "disclaimer": DISCLAIMER,
        }

    matches = rank_records(body.question, top_k=3)

    if matches:
        best = matches[0]

        answer = (
            f"The closest provision is {best['section_or_rule']} of "
            f"{best['document_name']} ({best['provision_title']}). "
            "See the matches below for related provisions."
        )

        answerable = True

    else:
        answer = (
            "No matching provision was found in the current GrahakNyay "
            "records. Please try different words or check official "
            "government sources."
        )

        answerable = False

    return {
        "name": body.name,
        "question": body.question,
        "answer": answer,
        "answerable": answerable,
        "matches": matches,
        "disclaimer": DISCLAIMER,
    }


# ---------------------------------------------------------------
# POST /chat
# ---------------------------------------------------------------


@app.post("/chat")
def chat_with_grahaknyay(body: ChatQuestion):
    """
    Answer a consumer question using:
    - GrahakNyay system prompt
    - Consumer question task prompt
    - Relevant legal records
    - Gemini or Groq through app/llm.py
    """

    # Read prompt files
    system_prompt = read_prompt("system.txt")
    task_prompt = read_prompt("task_consumer_question.txt")

    # Find relevant legal records
    matches = rank_records(body.question, top_k=3)

    # Prepare records as readable JSON
    context = json.dumps(matches, ensure_ascii=False, indent=2)

    # Fill the task prompt placeholders
    user_prompt = task_prompt.replace("{question}", body.question).replace(
        "{context}", context
    )

    # Combine system and task prompts
    complete_prompt = f"{system_prompt}\n\n{user_prompt}\n\nReminder: {DISCLAIMER}"

    try:
        # Generate response using the configured LLM provider
        ai_response = generate_response(complete_prompt)

        # Ensure the response has the required JSON fields
        return parse_chat_response(ai_response)

    except HTTPException:
        raise

    except Exception as error:
        logger.exception("chat_request_failed")
        raise HTTPException(
            status_code=502,
            detail="Unable to generate an answer right now. Please try again later.",
        ) from error


# ---------------------------------------------------------------
# GET /search/semantic?q=
# ---------------------------------------------------------------


@app.get("/search/semantic")
def semantic_search_api(
    q: str = Query(
        ..., min_length=1, description="Question to search in legal documents"
    ),
    top_k: int = Query(default=5, ge=1, le=20),
):
    """Search legal documents using semantic similarity."""

    results = semantic_search(q, top_k=top_k)

    return {"query": q, "count": len(results), "results": results}


# ---------------------------------------------------------------
# POST /ask
# ---------------------------------------------------------------
@app.post("/ask")
def ask_with_rag(body: ChatQuestion):
    """Answer a consumer question using RAG and safe optional caching."""

    cacheable = is_cacheable_question(body.question)
    cache_key = normalize_question(body.question) if cacheable else None

    if cache_key is not None:
        cached = get_cached_response(cache_key)

        if cached is not None:
            logger.info("rag_cache hit")
            cached["question"] = body.question
            return cached

        logger.info("rag_cache miss")
    else:
        logger.info("rag_cache bypass")

    try:
        result = answer_question(body.question)

        response = {
            "question": body.question,
            "answer": result["answer"],
            "citations": result["citations"],
            "disclaimer": DISCLAIMER,
        }

        if cache_key is not None:
            set_cached_response(cache_key, response)

        return response

    except Exception as error:
        logger.exception("rag_request_failed")
        raise HTTPException(
            status_code=502,
            detail="Unable to generate an answer right now. Please try again later.",
        ) from error

# --------------------------------------------------
# POST /agent - GrahakNyay LangGraph Agent
# --------------------------------------------------


class AgentRequest(BaseModel):
    question: str = Field(default="", max_length=2000)
    amount_paid: float | None = None
    cause_date: str | None = Field(default=None, max_length=50)
    thread_id: str | None = Field(default=None, max_length=100)
    approved: bool | None = None


@app.post("/agent")
def agent_endpoint(body: AgentRequest):
    """
    Run the GrahakNyay LangGraph agent.

    A calculator request first returns an approval request.
    Send the same thread_id with approved=true or false to resume.
    """

    # Resuming a paused approval request
    if body.approved is not None:
        if not body.thread_id:
            return {"error": "thread_id is required to resume approval."}

        return run_agent_graph(
            question=body.question, thread_id=body.thread_id, approved=body.approved
        )

    # Starting a new agent request
    thread_id = body.thread_id or str(uuid.uuid4())

    return run_agent_graph(
        question=body.question,
        amount_paid=body.amount_paid,
        cause_date=body.cause_date,
        thread_id=thread_id,
    )
