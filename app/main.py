
"""
GrahakNyay FastAPI service.

Run:
    python -m uvicorn app.main:app --reload

Docs:
    http://127.0.0.1:8000/docs
"""

import re
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

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


# ---------------------------------------------------------------
# Request model for POST /questions
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


# ---------------------------------------------------------------
# Check whether the question asks for a case decision timeline
# ---------------------------------------------------------------

def is_timeline_question(question):
    """
    Identify questions asking how long a consumer case will take.

    The current GrahakNyay dataset does not contain reliable
    case-specific decision timelines.
    """
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
    """
    Receive a consumer question and return relevant legal provisions.

    Case-decision timeline questions are not answered because the
    current dataset does not contain reliable case-specific timelines.
    """

    # Check for information not available in the current dataset.
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

    # Search for relevant records.
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
