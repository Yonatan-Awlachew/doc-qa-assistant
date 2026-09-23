# FILE: scripts/ask_cli.py
"""
Ask questions from the terminal, without the web API. Good for quick testing.
    python -m scripts.ask_cli
Type "exit" to stop.
"""
from app import config, rag, store


def main():
    vectors, chunks = store.load_index(config.INDEX_FOLDER)
    print(f"Index loaded: {len(chunks)} chunks. Type your question (or 'exit').")

    while True:
        question = input("\nQuestion: ").strip()
        if question.lower() in ("exit", "quit", ""):
            break

        result = rag.answer_question(question, vectors, chunks)
        print("\nAnswer:\n" + result["answer"])
        print("\nSources:")
        for s in result["sources"]:
            print(f"  [{s['number']}] {s['source']} p.{s['page']} (score {s['score']})")


if __name__ == "__main__":
    main()