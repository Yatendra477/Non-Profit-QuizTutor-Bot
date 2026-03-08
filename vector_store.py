"""
vector_store.py — ChromaDB wrapper for storing and retrieving donor email chunks.
Uses Google Generative AI embeddings for semantic search.
"""
from typing import List

from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

import config


def get_embedding_function() -> GoogleGenerativeAIEmbeddings:
    """Returns the Gemini embedding model instance."""
    return GoogleGenerativeAIEmbeddings(
        model=config.EMBEDDING_MODEL,
        google_api_key=config.GOOGLE_API_KEY,
    )


def build_vector_store(documents: List[Document]) -> Chroma:
    """
    Creates (or overwrites) the ChromaDB collection with the given documents.
    """
    embeddings = get_embedding_function()
    vector_store = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=config.CHROMA_DB_PATH,
        collection_name=config.CHROMA_COLLECTION_NAME,
    )
    return vector_store


def load_vector_store() -> Chroma:
    """
    Loads an existing persisted ChromaDB collection.
    Raises FileNotFoundError if the DB has not been ingested yet.
    """
    import os
    if not os.path.exists(config.CHROMA_DB_PATH):
        raise FileNotFoundError(
            f"ChromaDB not found at '{config.CHROMA_DB_PATH}'. "
            "Please run: python main.py --ingest"
        )
    embeddings = get_embedding_function()
    vector_store = Chroma(
        persist_directory=config.CHROMA_DB_PATH,
        embedding_function=embeddings,
        collection_name=config.CHROMA_COLLECTION_NAME,
    )
    return vector_store


def similarity_search(query: str, k: int = config.TOP_K_RETRIEVAL) -> List[Document]:
    """
    Retrieves the top-k most relevant document chunks for a given query.
    """
    store = load_vector_store()
    results = store.similarity_search(query, k=k)
    return results
