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

## 8. How to Run (Day 04)

### One-time setup (Windows PowerShell)

    cd GenAI-Developer-Journey
    .\.venv\Scripts\activate
    pip install -r requirements.txt

If `data/records.json` is missing, create it first:

    python -m app.parse_pdfs
    python -m app.ingest

### Start the GrahakNyay API

    uvicorn app.main:app --reload

The service runs at http://127.0.0.1:8000. Press Ctrl+C to stop it.
Interactive test page: http://127.0.0.1:8000/docs

### Endpoints

| Method | URL | What it does |
|---|---|---|
| GET | `/health` | Shows that the service is running and how many records are loaded |
| GET | `/records?limit=3` | Returns the first 3 records (default 10, maximum 100) |
| GET | `/records/{id}` | Returns one record. Returns 404 if the id does not exist |
| GET | `/search?q=mediation` | Ranks records using TF-IDF and cosine similarity |
| POST | `/questions` | Takes a consumer question and returns the closest provisions |

Example for `POST /questions` (send this in the /docs page):

    {"name": "Anshuman", "question": "My laptop stopped working and the seller refused to replace it"}

### Other commands

    python -m app.smart_search      # test the TF-IDF search from the terminal
    python analysis/explore.py      # print 3 facts about the records with pandas

### Notes
- Record ids (1 to 36) are added when the records are loaded. `data/records.json` is not changed.
- Search matches words, not meaning, so a question must share words with a provision to find it.
- This service gives general consumer-rights information and is not legal advice.

## 9. Semantic Search and Vector Database (Day 07)

Day 07 adds semantic search to GrahakNyay. It helps users find relevant legal information based on the meaning of their questions instead of matching only exact words.

### Data Pipeline (Day 07)

Official PDF documents → `app/chunking.py` → Document chunks → `app/embed.py` → Embeddings → `app/vectorstore.py` → Persistent ChromaDB collection

### Files and Their Purpose

| File | What it does |
|---|---|
| `app/chunking.py` | Splits legal PDF documents into smaller text chunks while keeping the document title, source filename and page number. |
| `app/embed.py` | Converts document text into numerical embeddings using an embedding model. |
| `app/vectorstore.py` | Stores document embeddings and metadata in a persistent ChromaDB collection and performs semantic searches. |
| `eval/run_search_eval.py` | Tests semantic search using 10 consumer questions. |
| `eval/search_results.md` | Stores the search results, including matching document sources and page numbers. |

### How to Run (Windows PowerShell)

Activate the virtual environment:

    .\.venv\Scripts\activate

Generate document chunks:

    python -m app.chunking

Generate embeddings:

    python -m app.embed

Create and index the persistent ChromaDB collection:

    python -m app.vectorstore

Run semantic search evaluation for 10 questions:

    python -m eval.run_search_eval

### Semantic Search API

Start the API:

    uvicorn app.main:app --reload

Open the Swagger UI:

    http://127.0.0.1:8000/docs

**Endpoint:**

| Method | URL | What it does |
|---|---|---|
| GET | `/search/semantic?q=your question` | Finds relevant legal document chunks using semantic similarity. |

Example:

    /search/semantic?q=What can I do if I purchased a defective laptop?

### Day 07 Results

- Successfully generated **152 document chunks**.
- Preserved document title, source filename and page number in chunk metadata.
- Generated embeddings successfully with 384 dimensions.
- Indexed all 152 chunks into a persistent ChromaDB collection.
- Tested semantic search with 10 consumer questions.
- Saved search evaluation results in `eval/search_results.md`.
- Successfully tested the semantic search API in Swagger UI with HTTP 200.

### Technologies Used

- Python
- PyPDF
- Sentence Transformers
- Embeddings
- ChromaDB
- FastAPI

### Known Limitations

- Search results depend on the quality of the document chunks and embeddings.
- Some PDF text may contain formatting or encoding issues.
- Semantic search retrieves relevant text but does not independently verify legal accuracy.
- GrahakNyay provides general consumer-rights information and is not legal advice.