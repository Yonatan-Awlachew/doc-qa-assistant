"""
All settings of the project live here.
Values are read from the .env file, so we never write the API key in the code.
"""
import os
from dotenv import load_dotenv

# Read the .env file and put its values into environment variables
load_dotenv()

# --- Chat (the model that writes the answer) ---
CHAT_PROVIDER = os.getenv("CHAT_PROVIDER", "gemini")      # "gemini" or "openai"
CHAT_MODEL = os.getenv("CHAT_MODEL", "gemini-2.5-flash")
CHAT_BASE_URL = os.getenv("CHAT_BASE_URL", "")             # only for "openai"
CHAT_API_KEY = os.getenv("CHAT_API_KEY", "")               # only for "openai"
CHAT_TEMPERATURE = float(os.getenv("CHAT_TEMPERATURE", "0.1"))   # 0 = most factual, 1 = most creative

# --- Embeddings (the model that turns text into vectors) ---
EMBED_PROVIDER = os.getenv("EMBED_PROVIDER", "gemini")    # "gemini" or "openai"
EMBED_MODEL = os.getenv("EMBED_MODEL", "gemini-embedding-001")
EMBED_BASE_URL = os.getenv("EMBED_BASE_URL", "")           # only for "openai"
EMBED_API_KEY = os.getenv("EMBED_API_KEY", "")             # only for "openai"

# --- Gemini key (used when a provider above is "gemini") ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# --- RAG settings ---
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))
TOP_K = int(os.getenv("TOP_K", "4"))

# --- Upload rules (NEW in v2) ---
ALLOWED_EXTENSIONS = [".pdf", ".docx", ".txt", ".md"]
MAX_FILE_MB = int(os.getenv("MAX_FILE_MB", "10"))
MAX_PAGES = int(os.getenv("MAX_PAGES", "300"))

# --- Where the app keeps its files (NEW in v2: all created at runtime) ---
UPLOADS_FOLDER = "storage/uploads"   # the original files, saved with a random name
INDEX_FOLDER = "storage/index"       # one sub-folder per document: vectors.npy + chunks.json
DB_PATH = "storage/app.db"           # SQLite database with the list of documents