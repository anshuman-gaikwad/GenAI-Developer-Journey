
"""
GrahakNyay FastAPI service.

Run:
    python -m uvicorn app.main:app --reload

Docs:
    http://127.0.0.1:8000/docs
"""

from app.vectorstore import semantic_search
import json
import re
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from app.llm import generate_response
from app.smart_search import RECORDS, rank_records


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
        description="The consumer's problem or question"
    )

    name: Optional[str] = Field(
        default=None,
        description="Consumer's name (optional)"
    )


class ChatQuestion(BaseModel):
    question: str = Field(
        ...,
        min_length=3,
        description="Ask a consumer-rights question"
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
            question
        )
    )

    mentions_case = bool(
        re.search(
            r"\b(case|commission|complaint|decision|decide)\b",
            question
        )
    )

    return asks_duration and mentions_case


# ---------------------------------------------------------------
# Helper: Read prompt files
# ---------------------------------------------------------------

def read_prompt(filename):
    prompt_path = PROMPTS_DIR / filename

    if not prompt_path.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Prompt file not found: {filename}"
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
            r"^```(?:json)?\s*",
            "",
            cleaned_text,
            flags=re.IGNORECASE
        )
        cleaned_text = re.sub(r"\s*```$", "", cleaned_text)

    try:
        result = json.loads(cleaned_text)

        answer = result.get("answer")
        confidence = result.get("confidence")
        follow_up = result.get("follow_up")

        if not isinstance(answer, str):
            raise ValueError("The answer field must be text.")

        if isinstance(confidence, bool) or not isinstance(
            confidence, (int, float)
        ):
            raise ValueError("Confidence must be a number.")

        confidence = float(confidence)

        if not 0.0 <= confidence <= 1.0:
            raise ValueError("Confidence must be between 0 and 1.")

        if follow_up is not None and not isinstance(follow_up, str):
            raise ValueError("Follow-up must be text or null.")

        return {
            "answer": answer,
            "confidence": confidence,
            "follow_up": follow_up
        }

    except (json.JSONDecodeError, ValueError, AttributeError):
        raise HTTPException(
            status_code=502,
            detail=(
                "The AI provider returned an invalid response. "
                "Please try again."
            )
        )


# ---------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------

@app.get("/health")
def health():
    """Check that the service is running."""
    return {
        "status": "ok",
        "records_loaded": len(RECORDS)
    }


# ---------------------------------------------------------------
# GET /records?limit=
# ---------------------------------------------------------------

@app.get("/records")
def list_records(
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
        description="How many records to return"
    )
):
    """Return the first 'limit' records."""
    return {
        "total": len(RECORDS),
        "returned": len(RECORDS[:limit]),
        "records": RECORDS[:limit]
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

    raise HTTPException(
        status_code=404,
        detail=f"Record {record_id} not found"
    )


# ---------------------------------------------------------------
# GET /search?q=
# ---------------------------------------------------------------

@app.get("/search")
def search(
    q: str = Query(
        ...,
        min_length=1,
        description="Words to search for"
    ),
    top_k: int = Query(
        default=5,
        ge=1,
        le=20,
        description="Maximum results"
    )
):
    """Search records using TF-IDF and cosine similarity."""
    results = rank_records(q, top_k=top_k)

    return {
        "query": q,
        "count": len(results),
        "results": results
    }


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
            "disclaimer": DISCLAIMER
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
        "disclaimer": DISCLAIMER
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
    context = json.dumps(
        matches,
        ensure_ascii=False,
        indent=2
    )

    # Fill the task prompt placeholders
    user_prompt = task_prompt.replace(
        "{question}", body.question
    ).replace(
        "{context}", context
    )

    # Combine system and task prompts
    complete_prompt = (
        f"{system_prompt}\n\n"
        f"{user_prompt}\n\n"
        f"Reminder: {DISCLAIMER}"
    )

    try:
        # Generate response using the configured LLM provider
        ai_response = generate_response(complete_prompt)

        # Ensure the response has the required JSON fields
        return parse_chat_response(ai_response)

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=f"AI provider request failed: {str(error)}"
        )





# ---------------------------------------------------------------
# GET /search/semantic?q=
# ---------------------------------------------------------------

@app.get("/search/semantic")
def semantic_search_api(
    q: str = Query(
        ...,
        min_length=1,
        description="Question to search in legal documents"
    ),
    top_k: int = Query(
        default=5,
        ge=1,
        le=20
    )
):
    """Search legal documents using semantic similarity."""

    results = semantic_search(q, top_k=top_k)

    return {
        "query": q,
        "count": len(results),
        "results": results
    }
