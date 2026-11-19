"""
rag.py - GrahakNyay Day 08

Retrieves relevant legal chunks and generates
answers with source citations.
"""

from app.llm import generate_response
from app.vectorstore import semantic_search


def answer_question(question, top_k=5):
    """
    Answer a consumer question using RAG.

    Returns:
        answer: Generated answer
        citations: Sources used for the answer
    """

    if not question or not question.strip():
        return {"answer": "Please enter a question.", "citations": []}

    # Step 1: Retrieve relevant legal chunks
    chunks = semantic_search(question, top_k=top_k)

    # Step 2: Check whether documents were retrieved
    if not chunks:
        return {
            "answer": (
                "I could not find relevant information in the "
                "available legal documents. Please try asking "
                "the question in a different way."
            ),
            "citations": [],
        }

    # Step 3: Prepare legal context
    context_parts = []
    citations = []

    for chunk in chunks:
        title = chunk.get("title", "Unknown document")
        source = chunk.get("source", "Unknown source")
        page = chunk.get("page", "Unknown page")
        content = chunk.get("text", "")

        if not content.strip():
            continue

        context_parts.append(
            f"""
Document: {title}
Source: {source}
Page: {page}

Content:
{content}
"""
        )

        citation = {"title": title, "source": source, "page": page}

        if citation not in citations:
            citations.append(citation)

    # Step 4: Check whether usable context exists
    if not context_parts:
        return {"answer": "No usable legal information was retrieved.", "citations": []}

    context = "\n".join(context_parts)

    # Step 5: Create the RAG prompt
    prompt = f"""
You are GrahakNyay, an assistant that explains
Indian consumer protection laws in simple language.

Answer the user's question using only the legal context
provided below.

IMPORTANT RULES:

1. Use only information supported by the legal context.
2. You may combine information from multiple relevant
   document chunks to answer one question.
3. Do not assume that information is missing just because
   it is spread across different chunks.
4. Explain the available information in simple language.
5. Do not invent legal sections, rules, fees, dates,
   procedures, or legal rights.
6. If only part of the question is supported, answer that
   part and clearly mention what information is missing.
7. If the context contains no information that answers
   the question, say that the available documents do not
   provide enough information.
8. Do not provide unsupported legal advice.

LEGAL CONTEXT:

{context}

USER QUESTION:

{question}

Write a clear and helpful answer:
"""

    # Step 6: Generate answer
    answer = generate_response(prompt)

    # Step 7: Return answer and citations
    return {"answer": answer.strip(), "citations": citations}
