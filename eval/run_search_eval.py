"""
run_search_eval.py - GrahakNyay Day 07

Tests semantic search using 10 consumer questions
and saves the results in search_results.md.
"""

from pathlib import Path

from app.vectorstore import semantic_search

QUESTIONS = [
    "What are my consumer rights in India?",
    "I purchased a defective laptop online. What can I do?",
    "What is a deficiency in service?",
    "What is an unfair trade practice?",
    "How can I file a consumer complaint?",
    "What is the right to be informed?",
    "What is product liability?",
    "Can I complain if an online seller refuses a refund?",
    "What is consumer mediation?",
    "How much time does a consumer commission take to decide a case?",
]


BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_FILE = BASE_DIR / "eval" / "search_results.md"


def run_evaluation():

    lines = [
        "# GrahakNyay Semantic Search Evaluation",
        "",
        "Embedding model: all-MiniLM-L6-v2",
        "Vector database: ChromaDB",
        "",
    ]

    for number, question in enumerate(QUESTIONS, start=1):
        print(f"\nTesting question {number}: {question}")

        results = semantic_search(question, top_k=3)

        lines.append(f"## {number}. {question}")
        lines.append("")

        if not results:
            lines.append("No matching chunks found.")
            lines.append("")
            continue

        for rank, result in enumerate(results, start=1):
            lines.append(f"### Result {rank}")
            lines.append(f"- **Title:** {result['title']}")
            lines.append(f"- **Source:** {result['source']}")
            lines.append(f"- **Page:** {result['page']}")
            lines.append(f"- **Distance:** {result['distance']:.4f}")
            lines.append(f"- **Text:** {result['text'][:500]}")
            lines.append("")

            print(f"  Result {rank}: {result['source']} (Page {result['page']})")

    OUTPUT_FILE.write_text("\n".join(lines), encoding="utf-8")

    print("\nEvaluation completed.")
    print("Results saved to:", OUTPUT_FILE)


if __name__ == "__main__":
    run_evaluation()
