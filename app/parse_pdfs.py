"""
parse_pdfs.py  -  Day 03 improvement

Reads the real government PDFs in data/raw/, finds the sections / rules
inside the text, and writes them to data/raw/records_parsed.json.

Next step in the pipeline: app/ingest.py cleans that file into data/records.json
"""

import json
import re
from pathlib import Path

from pypdf import PdfReader

# ---------------------------------------------------------------
# Folders
# ---------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
OUTPUT_FILE = RAW_DIR / "records_parsed.json"

# ---------------------------------------------------------------
# Document details (URLs are the same working URLs used in fetch.py)
# ---------------------------------------------------------------
ACT_FILE = "consumer_protection_act_2019.pdf"
ACT_NAME = "Consumer Protection Act, 2019"
ACT_URL = "https://consumeraffairs.gov.in/public/upload/files/CP%20Act%202019_1732700731.pdf"

RULES_FILE = "ecommerce_rules_2020.pdf"
RULES_NAME = "Consumer Protection (E-Commerce) Rules, 2020"
RULES_URL = "https://consumeraffairs.gov.in/public/upload/files/E%20commerce%20rules_1732703966.pdf"

AMEND_FILE = "ecommerce_amendment_rules_2021.pdf"
AMEND_NAME = "Consumer Protection (E-Commerce) (Amendment) Rules, 2021"
AMEND_URL = (
    "https://consumeraffairs.gov.in/public/upload/files/"
    "Consumer%20Protection%20%28E-Commerce%29%20%28Amendment%29%20Rules%2C%202021_1732704241.pdf"
)

# ---------------------------------------------------------------
# Which provisions we want.
# Format:  number : (title, who_it_helps, check_word)
# check_word = a word that MUST appear in the text we parsed from the PDF.
# If it does not appear, the parser prints a warning (a safety check).
# ---------------------------------------------------------------

# Definitions inside Section 2 of the Act, e.g. Section 2(7)
ACT_DEFINITIONS = {
    6: ("Complaint", "Consumers who want to know what a complaint can be about", "complaint"),
    7: ("Consumer", "People who buy goods or use services, including online buyers", "consumer"),
    9: ("Consumer Rights", "All consumers", "right"),
    10: ("Defect", "Consumers who bought faulty goods", "defect"),
    11: ("Deficiency", "Consumers facing poor or incomplete services", "deficiency"),
    16: ("E-Commerce", "Consumers who buy or sell online", "e-commerce"),
    46: ("Unfair Contract", "Consumers forced into one-sided contract terms", "unfair contract"),
    47: ("Unfair Trade Practice", "Consumers facing false claims or misleading selling methods", "unfair trade practice"),
}

# Whole sections of the Act, e.g. Section 34
ACT_SECTIONS = {
    21: ("Action Against False or Misleading Advertisements", "Consumers misled by advertisements", "advertisement"),
    34: ("Jurisdiction of District Commission", "Consumers deciding where to file a complaint", "District Commission"),
    35: ("Manner in Which Complaint Shall Be Made", "Consumers and consumer associations filing complaints", "complaint"),
    36: ("Proceedings Before District Commission", "Consumers and opposite parties in a complaint", "admit"),
    37: ("Reference to Mediation", "Parties who want to settle a dispute by mediation", "mediation"),
    38: ("Procedure on Admission of Complaint", "Consumers whose complaint has been admitted", "opposite party"),
    39: ("Findings of District Commission", "Consumers wanting to know what relief they can get", "replace"),
    41: ("Appeal Against Order of District Commission", "Parties who want to challenge a District Commission order", "State Commission"),
    47: ("Jurisdiction of State Commission", "Consumers approaching the State Commission", "State Commission"),
    51: ("Appeal to National Commission", "Parties challenging a State Commission order", "National Commission"),
    58: ("Jurisdiction of National Commission", "Consumers approaching the National Commission", "National Commission"),
    67: ("Appeal Against Order of National Commission", "Parties who want to go to the Supreme Court", "Supreme Court"),
    69: ("Limitation Period", "Consumers planning to file a complaint (time limit)", "two years"),
    71: ("Enforcement of Orders", "Consumers whose order must be enforced", "decree"),
    72: ("Penalty for Non-Compliance of Order", "Consumers when the seller ignores a Commission order", "imprisonment"),
    74: ("Establishment of Consumer Mediation Cell", "Consumers and businesses using mediation", "mediation cell"),
    80: ("Settlement Through Mediation", "Parties who reach a settlement through mediation", "settlement"),
    84: ("Liability of Product Manufacturer", "Consumers harmed by a defective product", "manufacturer"),
    89: ("Punishment for False or Misleading Advertisement", "Consumers misled by advertisements", "advertisement"),
    94: ("Measures to Prevent Unfair Trade Practices in E-Commerce", "Online shoppers and direct-selling customers", "e-commerce"),
}

# Rules of the E-Commerce Rules, 2020
ECOM_RULES = {
    2: ("Scope and Applicability", "Online consumers", "e-commerce"),
    3: ("Definitions", "Online consumers", "marketplace"),
    4: ("Duties of E-Commerce Entities", "Online consumers", "grievance"),
    5: ("Liabilities of Marketplace E-Commerce Entities", "Consumers buying on online marketplaces", "marketplace"),
    6: ("Duties of Sellers on Marketplace", "Consumers buying from sellers on online marketplaces", "seller"),
    7: ("Duties and Liabilities of Inventory E-Commerce Entities", "Consumers buying directly from online stores", "inventory"),
    8: ("Contravention of Rules", "Consumers whose e-commerce rights are violated", "Consumer Protection Act"),
}

# ---------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------

# Page header such as "SEC. 1] THE GAZETTE OF INDIA EXTRAORDINARY 3"
HEADER_PATTERN = re.compile(
    r"\d*\s*(SEC\. 1\]\s*)?THE GAZETTE OF INDIA\s*:?\s*EXTRAORDINARY(\s*\[P\s?ART II[—-]\s*(SEC\. 3\(i\)\])?)?\s*\d*"
)
# Cut everything after the signature of the notification
END_PATTERN = re.compile(r"\[\s*F\. No\..*$")


def read_pdf_text(pdf_path):
    """Read a PDF and return all its text as one string."""
    reader = PdfReader(pdf_path)
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return "\n".join(pages)


def remove_margin_notes(lines):
    """
    In the Act PDF, the small heading in the margin (for example
    'Review by District Commission in certain cases.') is extracted as
    several short lines at the END of the page. This removes such
    short trailing lines.
    """
    while len(lines) >= 2 and len(lines[-1]) <= 30 and len(lines[-2]) <= 30:
        lines = lines[:-1]
    return lines


def lines_to_text(lines):
    """Join lines into one clean paragraph."""
    text = " ".join(lines)
    text = HEADER_PATTERN.sub(" ", text)
    text = END_PATTERN.sub("", text)
    text = re.sub(r"(\w) -(\w)", r"\1-\2", text)   # "e -commerce" -> "e-commerce"
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def split_numbered_blocks(lines, pattern):
    """
    Walk through the lines. A new block starts when a line matches the
    pattern AND its number is exactly the next expected number (1, 2, 3...).
    The 'next number' check stops lines like '45 of 1860.' from being
    mistaken for a new section.
    Returns a dictionary:  number -> list of lines
    """
    blocks = {}
    expected = 1
    current = None

    for line in lines:
        match = re.match(pattern, line)
        if match and int(match.group(1)) == expected:
            current = expected
            blocks[current] = [line]
            expected += 1
        elif current is not None:
            blocks[current].append(line)

    return blocks


def make_summary(text, max_chars=320):
    """Use the start of the official text as a short summary."""
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars].rsplit(" ", 1)[0]
    return cut + " ..."


def check_word_present(word, text):
    return word.lower() in text.lower()


def build_record(title, doc_name, label, text, who, url):
    return {
        "provision_title": title,
        "document_name": doc_name,
        "section_or_rule": label,
        "plain_summary": make_summary(text),
        "who_it_helps": who,
        "source_url": url,
    }


# ---------------------------------------------------------------
# Parsing each document
# ---------------------------------------------------------------

def parse_act():
    """Parse the Consumer Protection Act, 2019."""
    records = []
    text = read_pdf_text(RAW_DIR / ACT_FILE)
    lines = text.split("\n")

    # Step 1: split the whole Act into sections 1, 2, 3 ... 107
    sections = split_numbered_blocks(lines, r"^(\d{1,3})\.\s")
    print(f"  Act: found {len(sections)} sections")

    # Step 2: definitions inside Section 2 -> clauses (1), (2) ... (47)
    section2_lines = remove_margin_notes(sections.get(2, []))
    clause_blocks = split_numbered_blocks(
        section2_lines[1:], r'^\((\d{1,2})\)\s+["\u201c]'
    )
    # The first clause starts after the line "2. In this Act, unless ..."
    for number, (title, who, check) in ACT_DEFINITIONS.items():
        if number not in clause_blocks:
            print(f"  WARNING: Section 2({number}) not found")
            continue
        clause_text = lines_to_text(clause_blocks[number])
        if not check_word_present(check, clause_text):
            print(f"  WARNING: Section 2({number}) text looks wrong")
            continue
        records.append(
            build_record(title, ACT_NAME, f"Section 2({number})", clause_text, who, ACT_URL)
        )

    # Step 3: whole sections
    for number, (title, who, check) in ACT_SECTIONS.items():
        if number not in sections:
            print(f"  WARNING: Section {number} not found")
            continue
        section_text = lines_to_text(remove_margin_notes(sections[number]))
        # remove the leading "34. "
        section_text = re.sub(r"^\d+\.\s*", "", section_text)
        if not check_word_present(check, section_text):
            print(f"  WARNING: Section {number} text looks wrong")
            continue
        records.append(
            build_record(title, ACT_NAME, f"Section {number}", section_text, who, ACT_URL)
        )

    return records


def english_part(text, marker):
    """The Gazette PDFs have Hindi first, then English. Keep only the English."""
    position = text.find(marker)
    if position == -1:
        return text
    return text[position:]


def parse_ecommerce_rules():
    """Parse the Consumer Protection (E-Commerce) Rules, 2020."""
    records = []
    text = english_part(read_pdf_text(RAW_DIR / RULES_FILE), "G.S.R. 462(E)")
    lines = text.split("\n")

    rules = split_numbered_blocks(lines, r"^(\d{1,2})\.\s")
    print(f"  E-Commerce Rules 2020: found {len(rules)} rules")

    for number, (title, who, check) in ECOM_RULES.items():
        if number not in rules:
            print(f"  WARNING: Rule {number} not found")
            continue
        rule_text = lines_to_text(rules[number])
        rule_text = re.sub(r"^\d+\.\s*", "", rule_text)
        # remove the repeated heading, e.g. "Duties of e-commerce entities. ---"
        rule_text = re.sub(
            "^" + re.escape(title) + r"[\s.:—–-]*", "", rule_text, flags=re.IGNORECASE
        )
        if not check_word_present(check, rule_text):
            print(f"  WARNING: Rule {number} text looks wrong")
            continue
        records.append(
            build_record(title, RULES_NAME, f"Rule {number}", rule_text, who, RULES_URL)
        )

    return records


def parse_amendment_rules():
    """Parse the 2021 amendment (it is very short, so we make one record)."""
    raw_text = read_pdf_text(RAW_DIR / AMEND_FILE)
    # lines_to_text() fixes extra spaces such as "E -Commerce" and cuts the signature
    text = lines_to_text(raw_text.split("\n"))
    text = english_part(text, "G.S.R. 328 (E)")

    start = text.find("2. In the Consumer Protection (E-Commerce) Rules, 2020")
    if start == -1:
        print("  WARNING: amendment rule 2 not found")
        return []

    body = re.sub(r"^2\.\s*", "", text[start:]).strip()

    print("  Amendment Rules 2021: found rule 2")
    return [
        build_record(
            "Nodal Officer Rule for E-Commerce Entities (Amendment)",
            AMEND_NAME,
            "Rule 2 (amends Rule 4(1) of 2020 Rules)",
            body,
            "Consumers who buy from e-commerce entities",
            AMEND_URL,
        )
    ]


# ---------------------------------------------------------------
# Main
# ---------------------------------------------------------------

def main():
    all_records = []

    for name, function in [
        ("Consumer Protection Act, 2019", parse_act),
        ("E-Commerce Rules, 2020", parse_ecommerce_rules),
        ("E-Commerce Amendment Rules, 2021", parse_amendment_rules),
    ]:
        print(f"\nParsing: {name}")
        try:
            all_records.extend(function())
        except FileNotFoundError as error:
            print("  File not found:", error)
        except Exception as error:  # a bad PDF must not stop the program
            print("  Could not parse:", error)

    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
            json.dump(all_records, file, indent=4, ensure_ascii=False)
    except OSError as error:
        print("File saving error:", error)
        return

    print("\nParsing completed!")
    print("Total records parsed from PDFs:", len(all_records))
    print("Saved file:", OUTPUT_FILE)


if __name__ == "__main__":
    main()