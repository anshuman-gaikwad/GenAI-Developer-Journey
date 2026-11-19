import json
from dataclasses import asdict
from pathlib import Path

from app.models import Record

# Project folder
BASE_DIR = Path(__file__).resolve().parent.parent

# Input and output file paths
RAW_FILE = BASE_DIR / "data" / "raw" / "records_parsed.json"
OUTPUT_FILE = BASE_DIR / "data" / "records.json"

# Required fields
REQUIRED_FIELDS = [
    "provision_title",
    "document_name",
    "section_or_rule",
    "plain_summary",
    "who_it_helps",
    "source_url",
]


def clean_records():
    cleaned_records = []

    try:
        with open(RAW_FILE, "r", encoding="utf-8") as file:
            raw_records = json.load(file)

    except FileNotFoundError:
        print("Error: records_parsed.json file not found.")
        return

    except json.JSONDecodeError:
        print("Error: Invalid JSON format.")
        return

    for row in raw_records:
        try:
            # Check required fields
            for field in REQUIRED_FIELDS:
                if field not in row or not isinstance(row[field], str):
                    raise ValueError(f"Missing or invalid field: {field}")

                row[field] = row[field].strip()

                if not row[field]:
                    raise ValueError(f"Empty field: {field}")

            # Create Record object
            record = Record(
                provision_title=row["provision_title"],
                document_name=row["document_name"],
                section_or_rule=row["section_or_rule"],
                plain_summary=row["plain_summary"],
                who_it_helps=row["who_it_helps"],
                source_url=row["source_url"],
            )

            cleaned_records.append(asdict(record))

        except (ValueError, TypeError, KeyError) as error:
            print("Skipping invalid record:", error)

    # Save cleaned records
    try:
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

        with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
            json.dump(cleaned_records, file, indent=4, ensure_ascii=False)

        print("Data cleaning completed!")
        print("Total valid records:", len(cleaned_records))
        print("Saved file:", OUTPUT_FILE)

    except OSError as error:
        print("File saving error:", error)


if __name__ == "__main__":
    clean_records()
