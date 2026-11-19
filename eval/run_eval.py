"""
run_eval.py - GrahakNyay Day 08

Evaluates RAG answers using two configurations.
"""

import json
from pathlib import Path

from app.rag import answer_question

BASE_DIR = Path(__file__).resolve().parent.parent
EVAL_FILE = BASE_DIR / "eval" / "eval_set.json"


def load_questions():
    """Load evaluation questions from JSON."""

    with open(EVAL_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def run_evaluation(config_name, top_k):
    """Run evaluation with a selected top-k value."""

    questions = load_questions()

    results = []
    successful = 0

    print(f"\nRunning configuration: {config_name}")
    print("Top K:", top_k)

    for item in questions:
        try:
            response = answer_question(item["question"], top_k=top_k)

            answer = response["answer"]
            citations = response["citations"]

            # Basic check: answer is not empty.
            passed = bool(answer.strip())

            if item["id"] == 10:
                passed = "i don't know" in answer.lower()

            if passed:
                successful += 1

            results.append(
                {
                    "id": item["id"],
                    "question": item["question"],
                    "answer": answer,
                    "citations": citations,
                    "passed": passed,
                }
            )

            print(f"Q{item['id']}: {'PASS' if passed else 'FAIL'}")

        except Exception as error:  # noqa: BLE001
            # Continue evaluating other questions if one fails.
            print(f"Q{item['id']}: ERROR - {error}")

            results.append(
                {
                    "id": item["id"],
                    "question": item["question"],
                    "answer": "",
                    "citations": [],
                    "passed": False,
                    "error": str(error),
                }
            )

    total = len(questions)
    accuracy = (successful / total) * 100 if total else 0

    print("\nConfiguration:", config_name)
    print("Passed:", successful, "/", total)
    print("Accuracy:", round(accuracy, 2), "%")

    return {
        "configuration": config_name,
        "top_k": top_k,
        "passed": successful,
        "total": total,
        "accuracy": round(accuracy, 2),
    }


if __name__ == "__main__":
    config_1 = run_evaluation(config_name="Config 1", top_k=3)

    config_2 = run_evaluation(config_name="Config 2", top_k=5)

    print("\n========== WINNER COMPARISON ==========")

    print("Config 1:", config_1)
    print("Config 2:", config_2)

    if config_1["accuracy"] > config_2["accuracy"]:
        print("\nWinner: Config 1")
    elif config_2["accuracy"] > config_1["accuracy"]:
        print("\nWinner: Config 2")
    else:
        print("\nBoth configurations have equal accuracy.")
