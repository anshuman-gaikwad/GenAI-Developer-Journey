# GrahakNyay — Resume Highlights

**Project:** GrahakNyay | Full-Stack Generative AI Consumer Rights Assistant

**Tech Stack:** Python, FastAPI, Streamlit, Groq, RAG, LangGraph, TF-IDF, Sentence Transformers, ChromaDB, Docker, GitHub Actions, pytest, Ruff

## Resume Bullets

- **Built and deployed** GrahakNyay, a full-stack GenAI consumer-rights assistant using FastAPI, Streamlit, Groq, and retrieval-augmented generation (RAG), delivering answers grounded in a knowledge base of **36 structured Indian consumer-law records** with source citations.

- **Developed an AI-powered legal assistance workflow** using LangGraph, integrating legal-document retrieval, Consumer Commission and filing-fee calculations, and a human-approval step before calculator execution; implemented a local semantic-search pipeline with **152 indexed document chunks**.

- **Improved application reliability and performance** by implementing request/token observability, input validation, prompt-injection precautions, and a five-minute response cache; achieved **37 passing automated tests** and reduced observed API latency from **1,004.23 ms to 1.22 ms** on a repeated local question, with GitHub Actions CI and Docker build checks.

## Interview Talking Points

**What problem does the project solve?**

Indian consumers often struggle to understand consumer-protection laws and complaint-filing procedures. GrahakNyay retrieves relevant legal provisions and generates understandable, source-referenced guidance.

**Why use RAG instead of relying only on an LLM?**

RAG provides relevant legal context to the model and supports citations, reducing reliance on the model's general knowledge. It does not guarantee that every generated answer is legally correct.

**Why use TF-IDF in production?**

The Render deployment has limited memory. TF-IDF offers a lightweight retrieval option, while the project also supports semantic retrieval locally.

**How did you measure performance?**

I logged API and LLM latency, along with available token usage. In one local two-request test, the first request took 1,004.23 ms and a repeated cached request took 1.22 ms. This is an illustrative result, not an average benchmark.

**What would you improve next?**

I would expand legal-answer evaluations, test prompt-injection defenses against live model behavior, add persistent shared caching, and improve monitoring and deployment reliability.

**Disclaimer:** GrahakNyay provides general consumer-rights information, not professional legal advice.