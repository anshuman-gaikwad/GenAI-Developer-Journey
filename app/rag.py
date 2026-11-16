
"""
rag.py - GrahakNyay Day 08

Retrieves relevant legal chunks and generates
answers with source citations.
"""

from app.vectorstore import semantic_search
from app.llm import generate_response


def answer_question(question, top_k=5):
    """
    Answer a consumer question using RAG.

    Returns:
        answer: Generated answer
        citations: Sources used for the answer
    """

    # Step 1: Retrieve relevant chunks
    chunks = semantic_search(question, top_k=top_k)

    # Step 2: If no relevant chunks are found
    if not chunks:
        return {
            "answer": "I don't know. The available legal documents do not contain enough information to answer this question.",
            "citations": []
        }

    # Step 3: Prepare legal context
    context_parts = []

    citations = []

    for chunk in chunks:
        context_parts.append(
            f"""
Document: {chunk['title']}
Source: {chunk['source']}
Page: {chunk['page']}

Content:
{chunk['text']}
"""
        )

        citation = {
            "title": chunk["title"],
            "source": chunk["source"],
            "page": chunk["page"]
        }

        if citation not in citations:
            citations.append(citation)

    context = "\n".join(context_parts)

    # Step 4: Create the RAG prompt
    prompt = f"""
You are GrahakNyay, an assistant that explains
Indian consumer protection laws in simple language.

Answer the user's question using ONLY the legal context
provided below.

Rules:
1. Do not make up legal information.
2. Answer only if the context directly supports the
   information requested in the question.
3. Do not use related information as a substitute
   for the exact information requested.
4. If the context does not directly answer the question,
   answer exactly: I don't know.
5. Explain the answer in simple language.
6. Do not give unsupported legal advice.
7. Use only the provided context.

Legal Context:
{context}

User Question:
{question}

Provide the answer:
"""

    # Step 5: Generate answer using Gemini or Groq
    answer = generate_response(prompt)

    # Step 6: Return answer and citations
    return {
        "answer": answer.strip(),
        "citations": citations
    }
