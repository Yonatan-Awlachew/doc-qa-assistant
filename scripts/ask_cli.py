"""
Ask questions from the terminal, without the web page. Good for quick testing.
    python -m scripts.ask_cli
It searches ALL uploaded documents. Type "exit" to stop.
"""
from app import database, rag


def main():
    documents = database.list_documents()
    print(f"{len(documents)} documents uploaded. Type your question (or 'exit').")

    while True:
        question = input("\nQuestion: ").strip()
        if question.lower() in ("exit", "quit", ""):
            break

        result = rag.ask(question)
        print("\nAnswer:\n" + result["answer"])
        print("\nSources:")
        for s in result["sources"]:
            print(f"  [{s['number']}] {s['source']} p.{s['page']} (score {s['score']})")


if __name__ == "__main__":
    main()