"""
smart_search.py  -  Day 04

Ranks GrahakNyay records for a question using:
  * TF-IDF         : gives each word a score (rare, meaningful words score higher)
  * cosine similarity : measures how close the question is to each record

It reads data/records.json (the 36 records parsed from the PDFs in Day 03).
"""

import json
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

BASE_DIR = Path(__file__).resolve().parent.parent
RECORDS_FILE = BASE_DIR / "data" / "records.json"


def load_records():
    """
    Read data/records.json and give every record an id (1, 2, 3 ...).
    records.json has no id field, so we add one here.
    The file itself is not changed.
    """
    try:
        with open(RECORDS_FILE, "r", encoding="utf-8") as file:
            rows = json.load(file)
    except FileNotFoundError:
        print("Error: data/records.json not found. Run: python -m app.ingest")
        return []
    except json.JSONDecodeError:
        print("Error: data/records.json is not valid JSON.")
        return []

    records = []
    for number, row in enumerate(rows, start=1):
        record = dict(row)
        record["id"] = number
        records.append(record)
    return records


# Load the records and build the TF-IDF table once, when the program starts
RECORDS = load_records()


def _record_text(record):
    """The text we compare against the question. Title is repeated so it counts more."""
    return " ".join(
        [
            record["provision_title"],
            record["provision_title"],
            record["section_or_rule"],
            record["plain_summary"],
            record["who_it_helps"],
        ]
    )


if RECORDS:
    VECTORIZER = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    MATRIX = VECTORIZER.fit_transform([_record_text(r) for r in RECORDS])
else:
    VECTORIZER = None
    MATRIX = None


def rank_records(query, top_k=5):
    """
    Return up to top_k records that best match the query,
    best first. Each result has an extra field: 'score' (0 to 1).
    Records with score 0 (no matching words) are not returned.
    """
    query = (query or "").strip()
    if not query or VECTORIZER is None:
        return []

    query_vector = VECTORIZER.transform([query])
    scores = cosine_similarity(query_vector, MATRIX).flatten()

    # Sort record positions by score, highest first
    order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

    results = []
    for position in order[:top_k]:
        if scores[position] <= 0:
            break
        item = dict(RECORDS[position])
        item["score"] = round(float(scores[position]), 4)
        results.append(item)
    return results


if __name__ == "__main__":
    # Quick test:  python -m app.smart_search
    question = "seller refused to replace my laptop"
    print("Question:", question)
    for item in rank_records(question, top_k=3):
        print(item["score"], "|", item["section_or_rule"], "|", item["provision_title"])