
"""
graph.py - GrahakNyay Day 09

LangGraph agent with:
1. RAG search
2. Commission and fee calculator
3. Short-term memory
4. One human approval step
"""

from typing import TypedDict, Optional, Any

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command

from app.rag import answer_question
from app.tools import commission_and_fee_finder


# 1. Define the graph state
class AgentState(TypedDict):
    question: str
    amount_paid: Optional[float]
    cause_date: Optional[str]
    selected_tool: str
    approved: Optional[bool]
    result: Any


# 2. Decide which tool to use
def decide_tool(state: AgentState):

    question = state["question"].lower()

    calculator_keywords = [
        "commission",
        "jurisdiction",
        "filing fee",
        "complaint fee",
        "last date",
        "deadline",
        "limitation period"
    ]

    use_calculator = any(
        word in question
        for word in calculator_keywords
    )

    if use_calculator:
        if state["amount_paid"] is None or state["cause_date"] is None:
            return {
                "selected_tool": "missing_details",
                "result": {
                    "message": (
                        "Please provide the amount paid and "
                        "the cause-of-action date (YYYY-MM-DD)."
                    )
                }
            }

        return {"selected_tool": "calculator"}

    return {"selected_tool": "rag"}


# 3. Ask for approval before calculator execution
def approval_step(state: AgentState):

    approved = interrupt({
        "message": "Please approve the commission and filing-fee calculation.",
        "amount_paid": state["amount_paid"],
        "cause_date": state["cause_date"]
    })

    return {"approved": bool(approved)}


# 4. Run the calculator
def calculator_node(state: AgentState):

    result = commission_and_fee_finder(
        state["amount_paid"],
        state["cause_date"]
    )

    return {"result": result}


# 5. Run RAG search
def rag_node(state: AgentState):

    result = answer_question(state["question"])

    return {"result": result}


# 6. Handle rejection
def rejected_node(state: AgentState):

    return {
        "result": {
            "message": "The user did not approve the calculation. No calculation was performed."
        }
    }


# 7. Route after deciding the tool
def route_tool(state: AgentState):

    if state["selected_tool"] == "calculator":
        return "approval"

    if state["selected_tool"] == "missing_details":
        return "end"

    return "rag"


# 8. Route after approval
def route_approval(state: AgentState):

    if state["approved"]:
        return "calculator"

    return "rejected"


# 9. Build the graph
builder = StateGraph(AgentState)

builder.add_node("decide", decide_tool)
builder.add_node("approval", approval_step)
builder.add_node("calculator", calculator_node)
builder.add_node("rag", rag_node)
builder.add_node("rejected", rejected_node)

builder.add_edge(START, "decide")

builder.add_conditional_edges(
    "decide",
    route_tool,
    {
        "approval": "approval",
        "rag": "rag",
        "end": END
    }
)

builder.add_conditional_edges(
    "approval",
    route_approval,
    {
        "calculator": "calculator",
        "rejected": "rejected"
    }
)

builder.add_edge("calculator", END)
builder.add_edge("rag", END)
builder.add_edge("rejected", END)


# 10. Add memory using a checkpointer
memory = InMemorySaver()

graph = builder.compile(checkpointer=memory)


# 11. Function used by FastAPI
def run_agent_graph(
    question,
    amount_paid=None,
    cause_date=None,
    thread_id="default-thread",
    approved=None
):

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    if approved is not None:
        # Continue a paused graph after user approval/rejection.
        result = graph.invoke(
            Command(resume=approved),
            config
        )

    else:
        # Start a new conversation.
        initial_state = {
            "question": question,
            "amount_paid": amount_paid,
            "cause_date": cause_date,
            "selected_tool": "",
            "approved": None,
            "result": None
        }

        result = graph.invoke(initial_state, config)

    # Check whether the graph is waiting for approval.
    if "__interrupt__" in result:

        approval_request = result["__interrupt__"][0]

        return {
            "status": "approval_required",
            "thread_id": thread_id,
            "approval_request": approval_request.value
        }

    return {
        "status": "completed",
        "thread_id": thread_id,
        "result": result.get("result")
    }
