"""
GrahakNyay smart search.

Uses TF-IDF and cosine similarity to rank consumer-law records.
Includes a relevance boost for Consumer Protection Act Section 2(7)
when the user asks who qualifies as a consumer.
"""

import json
import re
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

BASE_DIR = Path(__file__).resolve().parent.parent
RECORDS_FILE = BASE_DIR / "data" / "records.json"


def load_records():
    """Load records from data/records.json and assign IDs."""
    try:
        with open(RECORDS_FILE, "r", encoding="utf-8") as file:
            rows = json.load(file)

        if not isinstance(rows, list):
            print("Error: records.json must contain a list.")
            return []

    except FileNotFoundError:
        print("Error: data/records.json not found.")
        return []

    except json.JSONDecodeError:
        print("Error: data/records.json is not valid JSON.")
        return []

    records = []

    for number, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            continue

        record = dict(row)
        record["id"] = record.get("id", number)
        records.append(record)

    return records


# Load records when the application starts.
RECORDS = load_records()


def _record_text(record):
    """Prepare record text for TF-IDF search."""
    fields = [
        "provision_title",
        "provision_title",
        "document_name",
        "section_or_rule",
        "plain_summary",
        "who_it_helps",
    ]

    return " ".join(str(record.get(field, "")) for field in fields)


# Build the TF-IDF index.
VECTORIZER = None
MATRIX = None

if RECORDS:
    try:
        VECTORIZER = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))

        MATRIX = VECTORIZER.fit_transform([_record_text(record) for record in RECORDS])

    except ValueError as error:
        print("Could not build search index:", error)


def _is_consumer_definition_query(query):
    """Identify questions asking who is a consumer."""
    query = query.lower()

    patterns = [
        r"\bwho is considered a consumer\b",
        r"\bwho is a consumer\b",
        r"\bwho qualifies as a consumer\b",
        r"\bmeaning of consumer\b",
        r"\bdefinition of consumer\b",
        r"\bdefine consumer\b",
    ]

    return any(re.search(pattern, query) for pattern in patterns)


def _is_section_2_7(record):
    """Check whether a record is Section 2(7) of the Act."""
    section = str(record.get("section_or_rule", "")).lower()
    document = str(record.get("document_name", "")).lower()

    section_match = bool(re.search(r"section\s*2\s*[\(\[]\s*7\s*[\)\]]", section))

    act_match = "consumer protection act" in document and "e-commerce" not in document

    return section_match and act_match


def rank_records(query, top_k=5):
    """
    Rank records using TF-IDF and cosine similarity.

    A relevant Section 2(7) record receives an additional ranking
    boost when the question asks for the definition of a consumer.
    """
    query = (query or "").strip()

    if not query or VECTORIZER is None or MATRIX is None:
        return []

    query_vector = VECTORIZER.transform([query])
    similarities = cosine_similarity(query_vector, MATRIX).flatten()

    definition_query = _is_consumer_definition_query(query)

    ranked_records = []

    for position, similarity in enumerate(similarities):
        if similarity <= 0:
            continue

        record = RECORDS[position]

        # Start with the original cosine similarity.
        final_score = float(similarity)

        # Give Section 2(7) priority for consumer-definition questions.
        if definition_query and _is_section_2_7(record):
            final_score += 1.0

        item = dict(record)
        item["similarity"] = round(float(similarity), 4)
        item["score"] = round(final_score, 4)

        ranked_records.append(item)

    ranked_records.sort(key=lambda item: item["score"], reverse=True)

    return ranked_records[:top_k]


if __name__ == "__main__":
    question = "Who is considered a consumer under the Consumer Protection Act, 2019?"

    print("Question:", question)

    for record in rank_records(question, top_k=5):
        print(
            record["score"],
            "|",
            record["section_or_rule"],
            "|",
            record["provision_title"],
        )
