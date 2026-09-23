# FILE: eval/run_eval.py
"""
Measure how good the assistant is, with numbers (not just "it looks fine").
    python -m eval.run_eval

For each question in eval/questions.json we check two things:
  1. Retrieval hit: was the expected page among the retrieved chunks?
  2. Answer check:  does the answer contain all the expected keywords?
A question with "expected_source": null is a trick question: the right answer
is "I could not find this in the documents." (this tests hallucinations).
"""
import json
import time

from app import config, rag, store


def main():
    with open("eval/questions.json", "r", encoding="utf-8") as f:
        questions = json.load(f)

    vectors, chunks = store.load_index(config.INDEX_FOLDER)

    retrieval_hits = 0
    retrieval_total = 0
    answer_passes = 0
    results = []

    for number, item in enumerate(questions, start=1):
        result = rag.answer_question(item["question"], vectors, chunks)
        answer = result["answer"].lower()

        # 1. Retrieval check (only for questions that have an expected page)
        hit = None
        if item["expected_source"] is not None:
            retrieval_total += 1
            hit = False
            for s in result["sources"]:
                if s["source"] == item["expected_source"] and s["page"] == item["expected_page"]:
                    hit = True
            if hit:
                retrieval_hits += 1

        # 2. Answer check
        passed = True
        for keyword in item["expected_keywords"]:
            if keyword.lower() not in answer:
                passed = False
        if passed:
            answer_passes += 1

        print(f"Q{number}: retrieval={hit}  answer={'PASS' if passed else 'FAIL'}  -> {item['question']}")
        results.append({**item, "answer": result["answer"], "retrieval_hit": hit, "answer_pass": passed})

        time.sleep(4)  # free tier: stay under the requests-per-minute limit

    print("\n===== RESULTS =====")
    if retrieval_total > 0:
        print(f"Retrieval hit rate: {retrieval_hits}/{retrieval_total} = {retrieval_hits / retrieval_total:.0%}")
    print(f"Answer pass rate:   {answer_passes}/{len(questions)} = {answer_passes / len(questions):.0%}")

    with open("eval/results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("Details saved to eval/results.json")


if __name__ == "__main__":
    main()