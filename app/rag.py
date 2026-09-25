# FILE: app/rag.py
"""
Step 4 of RAG: Retrieve + Augment + Generate.
  1. Retrieve: find the chunks most similar to the question
  2. Augment:  put those chunks inside the prompt
  3. Generate: ask the LLM to answer using ONLY those chunks, with citations
"""
import time
from app import config, llm, store


def build_prompt(question, chunks):
    """Write the instructions + numbered context + question for the LLM."""
    context = ""
    for number, chunk in enumerate(chunks, start=1):
        context += f"[{number}] (file: {chunk['source']}, page {chunk['page']})\n{chunk['text']}\n\n"

    prompt = f"""You are an assistant that answers questions about documents.
Rules:
- Use ONLY the context below. Do not use outside knowledge.
- After each fact, write the number of the source in square brackets, like [1] or [2].
- If the answer is not in the context, reply exactly: "I could not find this in the documents."
- Answer in the same language as the question. Be short and clear.

Context:
{context}
Question: {question}
Answer:"""
    return prompt


def answer_question(question, vectors, chunks, top_k=None):
    """Full RAG pipeline for one question. Returns the answer and the sources used."""
    if top_k is None:
        top_k = config.TOP_K

    start_time = time.time()
    # 1. Retrieve
    question_vector = llm.embed_texts([question], task_type="RETRIEVAL_QUERY")[0]
    best_chunks = store.search(question_vector, vectors, chunks, top_k)

    # 2. Augment
    prompt = build_prompt(question, best_chunks)

    # 3. Generate
    answer = llm.generate_answer(prompt)

    sources = []
    for number, chunk in enumerate(best_chunks, start=1):
        sources.append({
            "number": number,
            "source": chunk["source"],
            "page": chunk["page"],
            "score": chunk["score"],
            "preview": chunk["text"][:200],
        })

    return {
        "question": question, 
        "answer": answer, 
        "sources": sources,
        "model": config.CHAT_MODEL,
        "seconds": round(time.time() - start_time,2),
        }