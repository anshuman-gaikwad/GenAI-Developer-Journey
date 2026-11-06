
from data.sample_records import records


# Load all records
def load_records():
    return records


# Search records by keyword
def search(keyword):
    keyword = keyword.strip().lower()

    if not keyword:
        return []

    found_records = []

    for record in records:
        searchable_text = " ".join(
            str(record[field])
            for field in [
                "provision_title",
                "document_name",
                "section_or_rule",
                "plain_summary",
                "who_it_helps",
                "category"
            ]
        ).lower()

        if keyword in searchable_text:
            found_records.append(record)

    return found_records


# Count records by category
def count_by():
    category_count = {}

    for record in records:
        category = record["category"]
        category_count[category] = category_count.get(category, 0) + 1

    return category_count


# Get record by ID
def get_by_id(record_id):
    for record in records:
        if record["id"] == record_id:
            return record

    return None
