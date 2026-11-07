# GrahakNyay

## 1. Product
GrahakNyay is a consumer rights assistance system. It helps consumers understand their rights and guides them on how to file complaints.

## 2. Target User
Online consumers, college students and people who face problems with purchased products or services.

**Example:** A college student purchases a laptop worth ₹38,000 online. After three weeks, it stops working, and the seller refuses to replace it.

## 3. Problem
Many consumers do not know their legal rights, which Consumer Commission to approach, what fees may apply and how to file a complaint.

## 4. Solution
GrahakNyay provides simple guidance to consumers based on consumer protection laws and rules.

## 5. Data Sources
- Consumer Protection Act, 2019
- Consumer Protection (Jurisdiction of District Commission, State Commission and National Commission) Rules, 2021
- National Consumer Helpline: https://consumerhelpline.gov.in/
- E-Jagriti Portal: https://e-jagriti.gov.in/

## 6. Technologies
- Python
- Git
- GitHub

## 7. Data Pipeline (Day 03)
The project builds its legal records from official government PDFs.

PDFs in data/raw/ -> app/parse_pdfs.py -> data/raw/records_parsed.json -> app/ingest.py -> data/records.json

| File | What it does |
|---|---|
| `app/fetch.py` | Downloads 3 official PDFs (CP Act 2019, E-Commerce Rules 2020, E-Commerce Amendment Rules 2021) into `data/raw/` |
| `app/parse_pdfs.py` | Reads the PDFs with pypdf and finds sections and rules in the text |
| `app/ingest.py` | Cleans the parsed rows into 6 fields and saves `data/records.json` |
| `app/models.py` | `Record` dataclass with the 6 fields |

**How to run (Windows PowerShell):**

    .\.venv\Scripts\activate
    python -m app.fetch
    python -m app.parse_pdfs
    python -m app.ingest

**Result:** `data/records.json` contains 36 records parsed from the PDFs.

**Known limits:**
- `plain_summary` is the start of the official legal text. It is not simplified yet.
- The Act PDF shows the old jurisdiction limits in Sections 34, 47 and 58. The 2021 Jurisdiction Rules changed them, so always verify current limits and fees on official sources.
- The India Code PDF link failed to download in my environment, so the Department of Consumer Affairs PDFs are used.
- This project gives general consumer-rights information and is not legal advice.