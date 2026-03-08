"""
config.py — Central configuration for the Non-Profit Quiz/Tutor Bot.
Reads API keys and settings from the .env file.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ─── LLM Settings ────────────────────────────────────────────────────────────
GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
LLM_MODEL: str = "gemini-2.5-flash"           # Latest Gemini model with higher free-tier quota
EMBEDDING_MODEL: str = "models/gemini-embedding-001"  # Gemini embedding model

# ─── ChromaDB Settings ───────────────────────────────────────────────────────
CHROMA_DB_PATH: str = "./chroma_db"
CHROMA_COLLECTION_NAME: str = "donor_emails"

# ─── Document Chunking Settings ──────────────────────────────────────────────
CHUNK_SIZE: int = 500        # Characters per chunk
CHUNK_OVERLAP: int = 80      # Overlap between chunks for context continuity

# ─── Quiz Settings ────────────────────────────────────────────────────────────
DEFAULT_NUM_QUESTIONS: int = 5
TOP_K_RETRIEVAL: int = 3     # Number of relevant chunks to retrieve for RAG

# ─── Data Path ────────────────────────────────────────────────────────────────
DATA_FILE: str = "./data/donor_emails.json"
