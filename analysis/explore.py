"""
explore.py  -  Day 04

Prints 3 facts about the GrahakNyay records using pandas.

Run:  python analysis/explore.py
"""

from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
RECORDS_FILE = BASE_DIR / "data" / "records.json"


def main():
    # Read data/records.json into a pandas table (DataFrame)
    try:
        df = pd.read_json(RECORDS_FILE, encoding="utf-8")
    except (FileNotFoundError, ValueError) as error:
        print("Could not read data/records.json:", error)
        print("Run these first: python -m app.parse_pdfs  and  python -m app.ingest")
        return

    print("========== GRAHAKNYAY RECORDS: 3 FACTS ==========")
    print(f"Total records: {len(df)}")

    # FACT 1: how many records come from each document
    print("\nFact 1: Records per document")
    per_document = df["document_name"].value_counts()
    for name, count in per_document.items():
        print(f"  {count:>3}  {name}")

    # FACT 2: which audience (who_it_helps) appears most often
    print("\nFact 2: Most common 'who_it_helps' groups (top 3)")
    top_audience = df["who_it_helps"].value_counts().head(3)
    for text, count in top_audience.items():
        print(f"  {count:>3}  {text}")

    # FACT 3: how long the summaries are, and how many were cut short
    print("\nFact 3: Summary length")
    lengths = df["plain_summary"].str.len()
    cut_short = df["plain_summary"].str.endswith("...").sum()
    longest_row = df.loc[lengths.idxmax()]
    shortest_row = df.loc[lengths.idxmin()]
    print(f"  Average length : {lengths.mean():.0f} characters")
    print(
        f"  Longest        : {lengths.max()} characters ({longest_row['section_or_rule']})"
    )
    print(
        f"  Shortest       : {lengths.min()} characters ({shortest_row['section_or_rule']})"
    )
    print(f"  Cut short with '...': {cut_short} of {len(df)} records")


if __name__ == "__main__":
    main()
