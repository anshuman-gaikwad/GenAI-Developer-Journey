"""
main.py  -  Day 04

GrahakNyay FastAPI service.

Run:   uvicorn app.main:app --reload
Docs:  http://127.0.0.1:8000/docs
"""

from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from app.smart_search import RECORDS, rank_records

app = FastAPI(
    title="GrahakNyay API",
    description="General consumer-rights information from Indian consumer law. Not legal advice.",
    version="0.1.0",
)

DISCLAIMER = (
    "This is general consumer-rights information, not legal advice. "
    "Please verify current rules and fees on official government sources."
)


# ---------------------------------------------------------------
# Data model for POST /questions
# ---------------------------------------------------------------
class Question(BaseModel):
    question: str = Field(..., min_length=3, description="The consumer's problem or question")
    name: Optional[str] = Field(default=None, description="Consumer's name (optional)")


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
def list_records(limit: int = Query(default=10, ge=1, le=100, description="How many records to return")):
    """Return the first 'limit' records (default 10)."""
    return {"total": len(RECORDS), "returned": len(RECORDS[:limit]), "records": RECORDS[:limit]}


# ---------------------------------------------------------------
# GET /records/{id}   (404 if missing)
# ---------------------------------------------------------------
@app.get("/records/{record_id}")
def get_record(record_id: int):
    """Return one record by its id. Returns 404 if the id does not exist."""
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
    """Rank records for the query using TF-IDF + cosine similarity."""
    results = rank_records(q, top_k=top_k)
    return {"query": q, "count": len(results), "results": results}


# ---------------------------------------------------------------
# POST /questions
# ---------------------------------------------------------------
@app.post("/questions")
def ask_question(body: Question):
    """Receive a consumer's question and return the most relevant legal provisions."""
    matches = rank_records(body.question, top_k=3)

    if matches:
        best = matches[0]
        answer = (
            f"The closest provision is {best['section_or_rule']} of "
            f"{best['document_name']} ({best['provision_title']}). "
            "See the matches below for related provisions."
        )
    else:
        answer = (
            "No matching provision was found. Try describing the problem with "
            "different words, for example: defective product, refund, complaint, e-commerce."
        )

    return {
        "name": body.name,
        "question": body.question,
        "answer": answer,
        "matches": matches,
        "disclaimer": DISCLAIMER,
    }