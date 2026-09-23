# app/llm.py
import time
from google import genai
from google.genai import types
from google.genai.errors import APIError

from app import config

client = None


def get_client():
    """Create the Gemini client only once, the first time we need it."""
    global client
    if client is None:
        if config.GEMINI_API_KEY in ("", "paste-your-key-here"):
            raise RuntimeError("GEMINI_API_KEY is missing. Put it in your .env file.")
        client = genai.Client(api_key=config.GEMINI_API_KEY)
    return client


def embed_texts(texts, task_type="RETRIEVAL_DOCUMENT", batch_size=20):
    """
    Turn a list of texts into a list of vectors.
    Uses exponential backoff on 429 Rate Limit errors.
    """
    vectors = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        
        # Retry loop for rate limits
        while True:
            try:
                result = get_client().models.embed_content(
                    model=config.EMBED_MODEL,
                    contents=batch,
                    config=types.EmbedContentConfig(task_type=task_type),
                )
                for embedding in result.embeddings:
                    vectors.append(embedding.values)
                break  # Batch succeeded, exit retry loop
            except APIError as e:
                if e.code == 429:
                    print("Rate limit hit. Waiting 60 seconds before retrying batch...")
                    time.sleep(60)
                else:
                    raise e

        # Throttle batch requests
        if i + batch_size < len(texts):
            time.sleep(2)

    return vectors


def generate_answer(prompt):
    """Send the prompt to the chat model and return its text answer."""
    response = get_client().models.generate_content(
        model=config.CHAT_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.1),
    )
    return response.text