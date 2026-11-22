# GrahakNyay

[![GrahakNyay CI](https://github.com/anshuman-gaikwad/GenAI-Developer-Journey/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/anshuman-gaikwad/GenAI-Developer-Journey/actions/workflows/ci.yml)

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


## 10. RAG and Answer Generation (Day 08)

Day 08 adds Retrieval-Augmented Generation (RAG) to GrahakNyay. It retrieves relevant legal information from document chunks and generates simple answers with source citations.

### Files and Their Purpose

| File | What it does |
|---|---|
| `app/rag.py` | Retrieves relevant chunks and generates answers with citations. |
| `app/llm.py` | Connects to the language model to generate answers. |
| `eval/eval_set.json` | Contains 15 consumer-related evaluation questions. |
| `eval/run_eval.py` | Evaluates RAG answers using two configurations. |
| `eval/prompt_compare.md` | Stores the prompt comparison and evaluation results. |

### RAG API Endpoint

| Method | URL | What it does |
|---|---|---|
| POST | `/ask` | Answers consumer questions using retrieved legal information and citations. |

Example question:

`What can a consumer do if a purchased product is defective?`

### Day 08 Evaluation Results

| Configuration | Top K | Passed | Total | Accuracy |
|---|---:|---:|---:|---:|
| Config 1 | 3 | 15 | 15 | 100% |
| Config 2 | 5 | 15 | 15 | 100% |

**Winner:** Both configurations achieved equal accuracy. Config 1 was selected because it retrieves fewer chunks.

### Important Features

- Retrieves relevant legal information using semantic search.
- Generates answers using the retrieved legal context.
- Provides document source and page citations.
- Responds with "I don't know" when the available context does not contain the answer.
- Provides general consumer-rights information, not legal advice.

### Technologies Used

- Python
- FastAPI
- ChromaDB
- Sentence Transformers
- Groq / Gemini API
- Retrieval-Augmented Generation (RAG)


## 11. Agent Tools and LangGraph (Day 09)

Day 09 adds an agent system to GrahakNyay. The agent chooses between
semantic legal search and a commission/filing-fee calculator.

### Files and Their Purpose

| File | What it does |
|---|---|
| `app/tools.py` | Finds the correct Consumer Commission, complaint fee and indicative filing deadline. |
| `app/agent_loop.py` | Hand-written agent that selects between RAG search and the calculator. |
| `app/graph.py` | Rebuilds the agent using LangGraph with memory and an approval step. |
| `app/main.py` | Provides the `POST /agent` API endpoint. |

### Legal Rules Used

- Jurisdiction: Consumer Protection (Jurisdiction of the District Commission, the State Commission and the National Commission) Rules, 2021.
- Complaint fee: Rule 7(2) of the Consumer Protection (Consumer Disputes Redressal Commissions) Rules, 2020, as amended in 2023.
- Limitation period: Section 69 of the Consumer Protection Act, 2019.

### How to Run

Activate the virtual environment:

    .\.venv\Scripts\activate

Install dependencies:

    pip install -r requirements.txt

Run the simple agent:

    python -m app.agent_loop

Start the API:

    uvicorn app.main:app --reload

Open Swagger:

    http://127.0.0.1:8000/docs

### Agent API

| Method | URL | What it does |
|---|---|---|
| POST | `/agent` | Runs the GrahakNyay LangGraph agent. |

The agent uses RAG for legal questions and the calculator for
commission, fee and filing-deadline questions.

Calculator requests pause for user approval before execution.
The same thread ID is used to resume the request.

### Important Limitations

- The two-year deadline is an indicative calculation based on the date supplied by the user.
- Section 69 allows delay to be condoned in appropriate cases.
- The user must provide the correct cause-of-action date.
- Commission jurisdiction is based on the value paid as consideration.
- LangGraph development memory uses an in-memory checkpointer and is cleared when the application restarts.
- GrahakNyay provides general consumer-rights information and is not legal advice.

## Day 10 — Streamlit User Interface

Day 10 focused on building a user-friendly interface for GrahakNyay using Streamlit.

### Features implemented

- **Consumer-rights chat:** Ask questions through a Streamlit chat interface connected to the FastAPI backend.
- **RAG and Agent modes:** Choose between the `/ask` and `/agent` endpoints.
- **Source citations:** Display legal document references with clickable links to official sources when available.
- **User feedback:** Thumbs up and thumbs down buttons save feedback in JSONL format.
- **Where do I file?:** Calculate the appropriate Consumer Commission, filing fee, and indicative complaint filing deadline.
- **API status:** Display the backend connection status in the sidebar.
- **Legal disclaimer:** Explain that generated responses are informational and not legal advice.

### Run the application locally

Start the FastAPI backend:

```bash
python -m uvicorn app.main:app --reload
```

Open another terminal and start Streamlit:

```bash
python -m streamlit run ui/app.py
```

Access the application:

- Streamlit UI: http://localhost:8501
- FastAPI documentation: http://localhost:8000/docs

**Implementation:** Completed. Final live UI verification should be performed before release.

---

## Day 11 — Testing, Code Quality and Docker

Day 11 focuses on automated testing, code quality, and containerizing GrahakNyay.

### S1 — Automated Testing and Ruff

**Status: Completed**

Created automated tests in the `tests/` directory.

Tests cover:

- API health endpoint (`/health`)
- Legal records retrieval
- Record limits and missing records
- Search endpoint (`/search`)
- RAG answer endpoint (`/ask`) using a fake response
- Invalid question validation
- Agent endpoint (`/agent`)
- Consumer Commission and filing fee calculations
- Date handling and invalid inputs

**Test results:**

```text
14 passed
```

Run the complete test suite:

```bash
python -m pytest -v
```

Run Ruff:

```bash
python -m ruff check .
```

Ruff verification result:

```text
All checks passed!
```

### S2 — Docker Containerization

**Status: Pending implementation and verification**

The following files will be added:

- `Dockerfile` — Defines the Python environment and application image.
- `.dockerignore` — Excludes unnecessary and sensitive files from the build context.
- `docker-compose.yml` — Configures the FastAPI and Streamlit services.

### Run with Docker

**Note:** Docker support is planned but has not yet been tested.

Once the Docker configuration is implemented, the intended startup command is:

```bash
docker compose up --build
```

Expected application URLs:

- Streamlit UI: http://localhost:8501
- FastAPI: http://localhost:8000
- API documentation: http://localhost:8000/docs

The Docker setup will be verified on a machine with Docker Desktop installed.

### Remaining work

- Create and configure the Docker files.
- Verify Docker image builds and dependency installation.
- Start the API and UI using Docker Compose.
- Test API connectivity, RAG responses, citations, and feedback persistence.
- Update this README after successful Docker verification.


## Live Deployment

**GrahakNyay** is deployed as a full-stack GenAI consumer-rights application.

- **Live Application (Streamlit):** https://genai-developer-journey-jowf6tq3safp6mu9dmzaey.streamlit.app/
- **Backend API (Render):** https://grahaknyay-api.onrender.com
- **Interactive API Documentation:** https://grahaknyay-api.onrender.com/docs

### Architecture

- **Frontend:** Streamlit Community Cloud
- **Backend:** FastAPI hosted on Render
- **Retrieval:** TF-IDF over 36 structured consumer-law records in production
- **LLM:** Groq
- **CI/CD:** GitHub Actions with Ruff, pytest, and Docker build checks

The frontend communicates with the backend over HTTPS. The backend retrieves relevant legal provisions and generates answers with citations.

*Note: Free hosting services may take additional time to respond after inactivity.*