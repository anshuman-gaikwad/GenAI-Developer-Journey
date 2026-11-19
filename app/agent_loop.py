"""
agent_loop.py - GrahakNyay Day 09

A simple hand-written agent that chooses between
RAG search and the commission/fee calculator.
"""

from app.rag import answer_question
from app.tools import commission_and_fee_finder


def run_agent(question, amount_paid=None, cause_date=None):
    """Choose and execute the required GrahakNyay tool."""

    question_lower = question.lower()

    calculator_keywords = [
        "commission",
        "jurisdiction",
        "filing fee",
        "complaint fee",
        "last date",
        "deadline",
        "limitation period",
    ]

    use_calculator = any(word in question_lower for word in calculator_keywords)

    # Tool 1: Commission and fee finder
    if use_calculator:
        if amount_paid is None or cause_date is None:
            return {
                "tool": "commission_and_fee_finder",
                "message": (
                    "Please provide the amount paid in rupees "
                    "and the cause-of-action date in YYYY-MM-DD format."
                ),
                "result": None,
            }

        result = commission_and_fee_finder(amount_paid, cause_date)

        return {"tool": "commission_and_fee_finder", "result": result}

    # Tool 2: Existing RAG search
    result = answer_question(question)

    return {"tool": "rag_search", "result": result}


if __name__ == "__main__":
    response = run_agent(
        question="Which commission should I approach and what is the filing fee?",
        amount_paid=38000,
        cause_date="2026-01-10",
    )

    print(response)
