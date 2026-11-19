"""
ui/app.py - GrahakNyay Day 10

Streamlit front-end for the GrahakNyay API (single-file version).

  1. Chat page: calls POST /ask (RAG) or POST /agent, shows clickable
     citations, and saves thumbs up / thumbs down to data/feedback.jsonl.
  2. "Where do I file?" page: enter the amount paid and the date of the
     problem -> Commission, filing fee and 2-year limitation date, each
     with a clickable rule citation.

Run (from the project root, with the API already running):

    uvicorn app.main:app --reload          # terminal 1
    streamlit run ui/app.py                # terminal 2
"""

import json
import os
import sys
import uuid
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import requests
import streamlit as st

# Project root, so "from app.tools import ..." works under Streamlit.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ==================================================================
# Citations -> clickable links
# ==================================================================

# File name in data/raw/  ->  (readable name, official URL)
# The URLs are the same ones app/fetch.py downloads from.
SOURCE_LINKS = {
    "consumer_protection_act_2019.pdf": (
        "Consumer Protection Act, 2019",
        (
            "https://consumeraffairs.gov.in/public/upload/files/"
            "CP%20Act%202019_1732700731.pdf"
        ),
    ),
    "ecommerce_rules_2020.pdf": (
        "Consumer Protection (E-Commerce) Rules, 2020",
        (
            "https://consumeraffairs.gov.in/public/upload/files/"
            "E%20commerce%20rules_1732703966.pdf"
        ),
    ),
    "ecommerce_amendment_rules_2021.pdf": (
        "Consumer Protection (E-Commerce) (Amendment) Rules, 2021",
        (
            "https://consumeraffairs.gov.in/public/upload/files/"
            "Consumer%20Protection%20%28E-Commerce%29%20%28Amendment%29"
            "%20Rules%2C%202021_1732704241.pdf"
        ),
    ),
}


def citation_link(citation):
    """
    Convert one citation dict into {"label": ..., "url": ... or None}.

    A PDF "#page=N" suffix makes most browsers open the exact page.
    """
    source = citation.get("source", "")
    page = citation.get("page")

    name, url = SOURCE_LINKS.get(
        source,
        (citation.get("title") or source or "Unknown source", None),
    )

    label = f"{name}, p. {page}" if page else name

    if url and page:
        url = f"{url}#page={page}"

    return {"label": label, "url": url}


def citation_markdown(citation):
    """Return a Markdown line: a clickable link when we know the URL."""
    link = citation_link(citation)

    if link["url"]:
        return f"[{link['label']}]({link['url']})"

    return link["label"]


# ==================================================================
# Where do I file? card logic
# ==================================================================

# ---- Official sources ------------------------------------------------
JURISDICTION_URL = (
    "https://consumeraffairs.nic.in/theconsumerprotection/"
    "consumer-protection-jurisdiction-district-commission-"
    "state-commission-and"
)

# G.S.R. 606(E), 17 Aug 2023: substitutes the fee table in Rule 7(2).
FEE_RULES_URL = "https://egazette.gov.in/WriteReadData/2023/248158.pdf"

# Section 69 is on page 28 of the Act PDF in data/raw/.
LIMITATION_URL = (
    "https://consumeraffairs.gov.in/public/upload/files/"
    "CP%20Act%202019_1732700731.pdf#page=28"
)

COMMISSION_RULE = {
    "District Commission": "Rule 3",
    "State Commission": "Rule 4",
    "National Commission": "Rule 5",
}

TIERS = [
    ("District Commission", "up to ₹50 lakh"),
    ("State Commission", "above ₹50 lakh, up to ₹2 crore"),
    ("National Commission", "above ₹2 crore"),
]


def format_inr(amount):
    """Format a number the Indian way: 3800000 -> '₹38,00,000'."""
    amount = round(float(amount))
    sign = "-" if amount < 0 else ""
    digits = str(abs(amount))

    if len(digits) <= 3:
        grouped = digits
    else:
        head, tail = digits[:-3], digits[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        grouped = ",".join(parts + [tail])

    return f"{sign}₹{grouped}"


def format_date(iso_text):
    """'2028-12-12' -> '12 Dec 2028'."""
    return date.fromisoformat(iso_text).strftime("%d %b %Y")


def build_card(calc, today=None):
    """
    Turn the calculator result (commission_and_fee_finder output)
    into the data the card displays.

    Returns {"ok": False, "error": text} when the calculator rejected the
    input, otherwise {"ok": True, ...}.
    """
    today = today or date.today()

    if not isinstance(calc, dict):
        return {"ok": False, "error": "No calculation result was returned."}

    if calc.get("error"):
        return {"ok": False, "error": calc["error"]}

    # The agent can also answer with a plain message (for example,
    # "please provide the amount and the date").
    if "commission" not in calc:
        return {
            "ok": False,
            "error": calc.get("message", "No calculation result was returned."),
        }

    commission = calc["commission"]
    fee = calc["filing_fee"]
    last_date = date.fromisoformat(calc["last_date_to_file"])
    days_left = (last_date - today).days

    rule = COMMISSION_RULE.get(commission, "")

    return {
        "ok": True,
        "amount_text": format_inr(calc["amount_paid"]),
        "cause_date_text": format_date(calc["cause_date"]),
        "commission": {
            "value": commission,
            "detail": dict(TIERS).get(commission, ""),
            "citation_text": (
                f"Jurisdiction Rules, 2021, {rule} (G.S.R. 912(E))"
                if rule
                else "Jurisdiction Rules, 2021"
            ),
            "citation_url": JURISDICTION_URL,
        },
        "fee": {
            "value": "Nil (₹0)" if fee == 0 else format_inr(fee),
            "detail": (
                "No fee up to ₹5 lakh" if fee == 0 else "Fee slab for the amount paid"
            ),
            "citation_text": (
                "CDRC Rules, 2020, Rule 7(2), as amended (G.S.R. 606(E), 2023)"
            ),
            "citation_url": FEE_RULES_URL,
        },
        "deadline": {
            "value": format_date(calc["last_date_to_file"]),
            "days_left": days_left,
            "expired": days_left < 0,
            "detail": calc.get("limitation_note", ""),
            "citation_text": "Consumer Protection Act, 2019, Section 69",
            "citation_url": LIMITATION_URL,
        },
        "tiers": TIERS,
        "selected": commission,
    }


# ==================================================================
# Feedback (thumbs up / down)
# ==================================================================

BASE_DIR = Path(__file__).resolve().parent.parent
FEEDBACK_FILE = BASE_DIR / "data" / "feedback.jsonl"


def save_feedback(rating, question, answer, citations=None, engine="ask", path=None):
    """Append one rating ("up" or "down"). Returns the saved record."""

    if rating not in ("up", "down"):
        raise ValueError("rating must be 'up' or 'down'")

    record = {
        "time": datetime.now(UTC).isoformat(timespec="seconds"),
        "rating": rating,
        "engine": engine,
        "question": question,
        "answer": answer,
        "citations": citations or [],
    }

    path = Path(path or FEEDBACK_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")

    return record


def feedback_counts(path=None):
    """Return {"up": n, "down": n} from the saved file."""

    counts = {"up": 0, "down": 0}
    path = Path(path or FEEDBACK_FILE)

    if not path.exists():
        return counts

    with open(path, encoding="utf-8") as file:
        for line in file:
            try:
                rating = json.loads(line).get("rating")
            except json.JSONDecodeError:
                continue
            if rating in counts:
                counts[rating] += 1

    return counts


# ==================================================================
# API client
# ==================================================================

CARD_QUESTION = (
    "Which commission should I approach, what is the filing fee "
    "and the last date to file my complaint?"
)


class ApiError(Exception):
    """The API could not be reached or returned an error."""

    def __init__(self, message, unreachable=False):
        super().__init__(message)
        self.unreachable = unreachable


def _post(base_url, path, payload, timeout):
    url = base_url.rstrip("/") + path

    try:
        response = requests.post(url, json=payload, timeout=timeout)
    except requests.exceptions.ConnectionError as error:
        raise ApiError(
            f"Cannot reach the API at {base_url}. Is uvicorn running?",
            unreachable=True,
        ) from error
    except requests.exceptions.Timeout as error:
        raise ApiError("The API took too long to respond.") from error

    if response.status_code != 200:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        raise ApiError(f"API error {response.status_code}: {detail}")

    try:
        return response.json()
    except ValueError as error:
        raise ApiError("The API returned invalid JSON.") from error


def health(base_url, timeout=3):
    """Return the /health JSON, or None when the API is down."""
    try:
        response = requests.get(base_url.rstrip("/") + "/health", timeout=timeout)
        return response.json() if response.status_code == 200 else None
    except (requests.exceptions.RequestException, ValueError):
        return None


def ask(base_url, question, timeout=120):
    """POST /ask -> {"answer", "citations", "disclaimer"}."""
    data = _post(base_url, "/ask", {"question": question}, timeout)

    return {
        "answer": data.get("answer", ""),
        "citations": data.get("citations", []),
        "disclaimer": data.get("disclaimer"),
    }


def agent_chat(base_url, question, timeout=120):
    """
    POST /agent for a normal chat question.
    Returns the same shape as ask().
    """
    data = _post(
        base_url,
        "/agent",
        {"question": question, "thread_id": str(uuid.uuid4())},
        timeout,
    )

    if data.get("error"):
        raise ApiError(data["error"])

    if data.get("status") == "approval_required":
        return {
            "answer": (
                "This question needs the filing calculator. Please use "
                "the 'Where do I file?' page and enter the amount and date."
            ),
            "citations": [],
            "disclaimer": None,
        }

    result = data.get("result") or {}

    # RAG result
    if "answer" in result:
        return {
            "answer": result["answer"],
            "citations": result.get("citations", []),
            "disclaimer": None,
        }

    # Agent asked for more details (amount paid / date)
    return {
        "answer": result.get(
            "message",
            "The agent could not answer this question.",
        )
        + " You can use the 'Where do I file?' page for this.",
        "citations": [],
        "disclaimer": None,
    }


def filing_calculation(base_url, amount_paid, cause_date, timeout=120):
    """
    Run the commission/fee/deadline calculation through POST /agent.

    The agent pauses for approval first. In the UI the person's click on
    "Find where to file" is that approval, so we resume it with
    approved=True using the same thread_id.
    """
    thread_id = str(uuid.uuid4())

    first = _post(
        base_url,
        "/agent",
        {
            "question": CARD_QUESTION,
            "amount_paid": float(amount_paid),
            "cause_date": cause_date,
            "thread_id": thread_id,
        },
        timeout,
    )

    if first.get("error"):
        raise ApiError(first["error"])

    if first.get("status") == "approval_required":
        final = _post(
            base_url,
            "/agent",
            {
                "question": CARD_QUESTION,
                "thread_id": first.get("thread_id", thread_id),
                "approved": True,
            },
            timeout,
        )
    else:
        final = first

    if final.get("error"):
        raise ApiError(final["error"])

    return final.get("result") or {}


# ==================================================================
# Streamlit app
# ==================================================================

DEFAULT_API = os.getenv("GRAHAKNYAY_API", "http://127.0.0.1:8000")

DISCLAIMER = (
    "General consumer-rights information, not legal advice. "
    "Please verify current rules and fees on official government sources."
)

EXAMPLES = [
    "What can I do if a laptop I bought online stops working?",
    "What is an unfair trade practice?",
    "Can I get a refund if an e-commerce seller cancels my order?",
]

PAGE_CHAT = "💬 Ask GrahakNyay"
PAGE_FILE = "📍 Where do I file?"


# ------------------------------------------------------------------
# Session state
# ------------------------------------------------------------------


def init_state():
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("filing", None)


# ------------------------------------------------------------------
# Feedback
# ------------------------------------------------------------------


def rate_message(message_id, rating):
    """Callback for the thumbs buttons: save the rating to disk."""
    for index, message in enumerate(st.session_state.messages):
        if message["id"] != message_id or message.get("rating"):
            continue

        # The question is the user message just before this answer.
        question = ""
        if index > 0:
            question = st.session_state.messages[index - 1]["content"]

        save_feedback(
            rating=rating,
            question=question,
            answer=message["content"],
            citations=message.get("citations", []),
            engine=message.get("engine", "ask"),
        )
        message["rating"] = rating
        return


# ------------------------------------------------------------------
# Chat page
# ------------------------------------------------------------------


def render_message(message):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message["role"] != "assistant":
            return

        citations = message.get("citations", [])
        if citations:
            st.markdown("**Sources**")
            for citation in citations:
                st.markdown(f"- {citation_markdown(citation)}")

        if message.get("error"):
            return

        rating = message.get("rating")
        if rating:
            st.caption(
                "👍 Thanks for the feedback!"
                if rating == "up"
                else "👎 Thanks - we will use this to improve."
            )
        else:
            col_up, col_down, _ = st.columns([1, 1, 8])
            col_up.button(
                "👍",
                key=f"up_{message['id']}",
                on_click=rate_message,
                args=(message["id"], "up"),
            )
            col_down.button(
                "👎",
                key=f"down_{message['id']}",
                on_click=rate_message,
                args=(message["id"], "down"),
            )


def get_answer(question, base_url, engine):
    """Call the API and return an assistant message dict."""
    message = {
        "id": str(uuid.uuid4()),
        "role": "assistant",
        "engine": "agent" if engine.startswith("Agent") else "ask",
    }

    try:
        if message["engine"] == "agent":
            data = agent_chat(base_url, question)
        else:
            data = ask(base_url, question)

        message["content"] = data["answer"] or "I don't know."
        message["citations"] = data["citations"]

    except ApiError as error:
        message["content"] = f"⚠️ {error}"
        message["citations"] = []
        message["error"] = True

    return message


def chat_page(base_url, engine):
    st.title("⚖️ GrahakNyay")
    st.caption("Ask a consumer-rights question. " + DISCLAIMER)

    if not st.session_state.messages:
        st.markdown("**Try one of these:**")
        for example in EXAMPLES:
            if st.button(example, key=f"ex_{example}"):
                st.session_state.pending = example
                st.rerun()

    for message in st.session_state.messages:
        render_message(message)

    question = st.chat_input("Ask about your consumer rights...")
    question = question or st.session_state.pop("pending", None)

    if question:
        st.session_state.messages.append(
            {
                "id": str(uuid.uuid4()),
                "role": "user",
                "content": question,
            }
        )
        with st.spinner("Searching the legal documents..."):
            answer = get_answer(question, base_url, engine)
        st.session_state.messages.append(answer)
        st.rerun()


# ------------------------------------------------------------------
# "Where do I file?" card
# ------------------------------------------------------------------


def run_filing_lookup(base_url, amount, cause_date):
    """Use /agent; fall back to the local calculator if the API is down."""
    iso_date = cause_date.isoformat()

    try:
        return filing_calculation(base_url, amount, iso_date), "api"
    except ApiError as error:
        if not error.unreachable:
            raise

    # Offline fallback: the same Day 09 calculator, called directly.
    from app.tools import commission_and_fee_finder

    return commission_and_fee_finder(amount, iso_date), "local"


def show_card(card):
    with st.container(border=True):
        st.subheader("📍 Where do I file?")
        st.caption(
            f"Amount paid {card['amount_text']} · "
            f"problem arose on {card['cause_date_text']}"
        )

        col_commission, col_fee, col_deadline = st.columns(3)

        commission = card["commission"]
        with col_commission:
            st.metric("File with", commission["value"])
            st.caption(commission["detail"])
            st.markdown(
                f"[{commission['citation_text']}]({commission['citation_url']})"
            )

        fee = card["fee"]
        with col_fee:
            st.metric("Filing fee", fee["value"])
            st.caption(fee["detail"])
            st.markdown(f"[{fee['citation_text']}]({fee['citation_url']})")

        deadline = card["deadline"]
        with col_deadline:
            st.metric("Last date to file", deadline["value"])
            if deadline["expired"]:
                st.caption(f"⚠️ {abs(deadline['days_left'])} days past")
            else:
                st.caption(f"{deadline['days_left']} days left")
            st.markdown(f"[{deadline['citation_text']}]({deadline['citation_url']})")

        st.markdown("---")
        ladder = []
        for name, limit in card["tiers"]:
            text = f"{name} ({limit})"
            ladder.append(f"**→ {text}**" if name == card["selected"] else text)
        st.markdown("  ·  ".join(ladder))

        if deadline["expired"]:
            st.warning(
                "The two-year period appears to be over. Section 69(2) lets "
                "the Commission accept a late complaint if you show "
                "sufficient cause - ask a consumer helpline or lawyer."
            )
        st.caption(deadline["detail"])
        st.caption(
            "Based on the amount paid as consideration. The deadline is "
            "indicative and depends on the correct cause-of-action date. " + DISCLAIMER
        )


def filing_page(base_url):
    st.title("📍 Where do I file?")
    st.caption(
        "Enter what you paid and when the problem started. "
        "Clicking the button approves the calculation."
    )

    with st.form("filing_form"):
        col_amount, col_date = st.columns(2)
        amount = col_amount.number_input(
            "Amount paid (₹)",
            min_value=1,
            value=38000,
            step=1000,
        )
        cause_date = col_date.date_input(
            "Date the problem arose (cause of action)",
            value=date.today() - timedelta(days=21),
            max_value=date.today(),
        )
        submitted = st.form_submit_button("Find where to file")

    if submitted:
        try:
            with st.spinner("Calculating..."):
                calc, source = run_filing_lookup(base_url, amount, cause_date)
            card = build_card(calc)
            card["source"] = source
            st.session_state.filing = card
        except ApiError as error:
            st.session_state.filing = {"ok": False, "error": str(error)}

    card = st.session_state.filing

    if card is None:
        st.info(
            f"Example: a laptop bought for {format_inr(38000)} -> District Commission."
        )
        return

    if not card["ok"]:
        st.error(card["error"])
        return

    show_card(card)

    if card.get("source") == "local":
        st.caption("API not reachable - calculated locally with app/tools.py.")


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------


def sidebar():
    with st.sidebar:
        st.header("GrahakNyay")

        page = st.radio("Page", [PAGE_CHAT, PAGE_FILE])

        st.markdown("---")
        base_url = st.text_input("API address", DEFAULT_API)

        info = health(base_url)
        if info:
            st.success(f"API online · {info.get('records_loaded', '?')} records")
        else:
            st.error("API offline - start uvicorn")

        engine = st.radio(
            "Chat uses",
            ["Ask (RAG) → /ask", "Agent → /agent"],
        )

        counts = feedback_counts()
        st.caption(f"Feedback saved: 👍 {counts['up']} · 👎 {counts['down']}")

        if st.button("Clear chat"):
            st.session_state.messages = []
            st.rerun()

        st.markdown("---")
        st.caption(DISCLAIMER)

    return page, base_url, engine


def main():
    st.set_page_config(page_title="GrahakNyay", page_icon="⚖️", layout="wide")
    init_state()
    page, base_url, engine = sidebar()

    if page == PAGE_FILE:
        filing_page(base_url)
    else:
        chat_page(base_url, engine)


main()
