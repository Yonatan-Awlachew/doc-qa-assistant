"""
Everything that talks to an AI provider is in this file.
  - embed_texts(): turns text into vectors (lists of numbers)
  - generate_answer(): asks the LLM to write an answer

Two kinds of provider are supported (you choose in the .env file):
  - "gemini" -> Google Gemini, with the google-genai library
  - "openai" -> ANY service that speaks the "OpenAI format":
                OpenAI, Groq, OpenRouter, Mistral, Ollama (local, free)...
                Only the address (base URL), the key and the model name change.

Chat and embeddings can use DIFFERENT providers
(for example: Groq for chat + Gemini for embeddings).
"""
import time

from google import genai
from google.genai import types
from openai import OpenAI

from app import config

# The clients are created only once, the first time we need them
gemini_client = None
openai_chat_client = None
openai_embed_client = None


# ---------- create the clients ----------

def get_gemini_client():
    global gemini_client
    if gemini_client is None:
        if config.GEMINI_API_KEY == "" or config.GEMINI_API_KEY == "paste-your-key-here":
            raise RuntimeError("GEMINI_API_KEY is missing. Put it in your .env file.")
        gemini_client = genai.Client(api_key=config.GEMINI_API_KEY)
    return gemini_client


def get_openai_chat_client():
    global openai_chat_client
    if openai_chat_client is None:
        if config.CHAT_API_KEY == "":
            raise RuntimeError("CHAT_API_KEY is missing. Put your Groq key in the .env file.")
        openai_chat_client = OpenAI(base_url=config.CHAT_BASE_URL, api_key=config.CHAT_API_KEY)
    return openai_chat_client


def get_openai_embed_client():
    global openai_embed_client
    if openai_embed_client is None:
        if config.EMBED_API_KEY == "":
            raise RuntimeError("EMBED_API_KEY is missing. Put it in the .env file.")
        openai_embed_client = OpenAI(base_url=config.EMBED_BASE_URL, api_key=config.EMBED_API_KEY)
    return openai_embed_client


# ---------- embeddings ----------

def embed_texts(texts, task_type="RETRIEVAL_DOCUMENT", batch_size=20):
    """
    Turn a list of texts into a list of vectors.
    task_type is "RETRIEVAL_DOCUMENT" for chunks and "RETRIEVAL_QUERY" for questions
    (only Gemini uses it; the others ignore it).
    We send the texts in small batches so we do not hit the API limits.
    """
    vectors = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]

        if config.EMBED_PROVIDER == "gemini":
            result = get_gemini_client().models.embed_content(
                model=config.EMBED_MODEL,
                contents=batch,
                config=types.EmbedContentConfig(task_type=task_type),
            )
            for embedding in result.embeddings:
                vectors.append(embedding.values)

        elif config.EMBED_PROVIDER == "openai":
            result = get_openai_embed_client().embeddings.create(
                model=config.EMBED_MODEL,
                input=batch,
                encoding_format="float",
            )
            for item in result.data:
                vectors.append(item.embedding)

        else:
            raise ValueError(f"Unknown EMBED_PROVIDER: {config.EMBED_PROVIDER}")

        if i + batch_size < len(texts):
            time.sleep(1)  # small pause: free tiers have rate limits

    return vectors


# ---------- chat ----------

def call_chat_model(prompt):
    """Send the prompt to the chat model once and return its text answer."""
    if config.CHAT_PROVIDER == "gemini":
        response = get_gemini_client().models.generate_content(
            model=config.CHAT_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=config.CHAT_TEMPERATURE),
        )
        return response.text

    elif config.CHAT_PROVIDER == "openai":
        response = get_openai_chat_client().chat.completions.create(
            model=config.CHAT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=config.CHAT_TEMPERATURE,
        )
        return response.choices[0].message.content

    else:
        raise ValueError(f"Unknown CHAT_PROVIDER: {config.CHAT_PROVIDER}")


# Errors that usually go away if we wait a little:
# 503 = the model is overloaded, 429 = we sent too many requests (rate limit)
TEMPORARY_ERRORS = ["503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED", "overloaded"]


def is_temporary(error):
    message = str(error)
    for word in TEMPORARY_ERRORS:
        if word in message:
            return True
    return False


def generate_answer(prompt, max_tries=3):
    """
    Call the chat model. If it fails with a TEMPORARY error, wait and try again
    (2 s, then 4 s). Permanent errors (for example a wrong API key) fail at once.
    """
    for attempt in range(1, max_tries + 1):
        try:
            return call_chat_model(prompt)
        except Exception as error:
            if attempt == max_tries or not is_temporary(error):
                raise
            wait_seconds = 2 * attempt
            print(f"Temporary LLM error (try {attempt}/{max_tries}), retrying in {wait_seconds} s: {error}")
            time.sleep(wait_seconds)