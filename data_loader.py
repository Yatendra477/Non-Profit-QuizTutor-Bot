"""
data_loader.py — Loads donor emails and splits them into overlapping chunks.
Returns LangChain Document objects ready for embedding.
"""
import json
from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

import config


def load_donor_emails(filepath: str = config.DATA_FILE) -> List[Document]:
    """
    Reads donor_emails.json and returns a list of LangChain Documents.
    Each document's metadata carries email id, subject, from, and date.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        emails: List[dict] = json.load(f)

    documents: List[Document] = []
    for email in emails:
        # Combine subject + body as the page content for richer context
        page_content = f"Subject: {email['subject']}\n\n{email['body']}"
        metadata = {
            "id": email["id"],
            "subject": email["subject"],
            "from": email["from"],
            "date": email["date"],
        }
        documents.append(Document(page_content=page_content, metadata=metadata))

    return documents


def chunk_documents(documents: List[Document]) -> List[Document]:
    """
    Splits documents into overlapping chunks for more granular retrieval.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        length_function=len,
    )
    chunks = splitter.split_documents(documents)
    return chunks


if __name__ == "__main__":
    docs = load_donor_emails()
    print(f"Loaded {len(docs)} emails.")
    chunks = chunk_documents(docs)
    print(f"Split into {len(chunks)} chunks.")
    print("\nSample chunk:\n", chunks[0].page_content[:300])
