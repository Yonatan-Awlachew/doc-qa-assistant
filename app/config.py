"""
All settings of the project live here.
Values are read from the .env file, so we never write the API key in the code.
"""
import os
from dotenv import load_dotenv

# Read the .env file and put its values into environment variables

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gemini-3.6-flash")
EMBED_MODEL = os.getenv("EMBED_MODEL", "gemini-embedding-001")

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))
TOP_K = int(os.getenv("TOP_K", "4"))

# Folders
DOCS_FOLDER = "data/doc"
INDEX_FOLDER = "data/index"
