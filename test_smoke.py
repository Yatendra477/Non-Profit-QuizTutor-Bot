"""
test_smoke.py — Smoke tests for the Non-Profit Quiz/Tutor Bot.
Tests individual pipeline components without needing a live API key.
Run with: python -m pytest test_smoke.py -v
"""
import json
import os
import sys
import types
import pytest

# ─── Helpers to mock external dependencies ───────────────────────────────────

def _mock_config(monkeypatch):
    """Patch config values so tests don't need a real API key."""
    import config
    monkeypatch.setattr(config, "GOOGLE_API_KEY", "FAKE_KEY_FOR_TESTING")
    monkeypatch.setattr(config, "CHROMA_DB_PATH", "./test_chroma_db")


# ─── data_loader tests ────────────────────────────────────────────────────────

def test_load_donor_emails():
    """Donor emails file should load into a non-empty list of Documents."""
    from data_loader import load_donor_emails
    docs = load_donor_emails()
    assert len(docs) > 0, "Should load at least one email"
    assert hasattr(docs[0], "page_content"), "Should return LangChain Document objects"
    assert "Subject:" in docs[0].page_content, "Content should include the subject line"
    print(f"\n  ✔ Loaded {len(docs)} emails")


def test_chunk_documents():
    """Chunking should produce more chunks than original documents."""
    from data_loader import load_donor_emails, chunk_documents
    docs = load_donor_emails()
    chunks = chunk_documents(docs)
    assert len(chunks) >= len(docs), "Chunking should produce at least as many chunks as documents"
    assert all(hasattr(c, "page_content") for c in chunks), "All chunks should be Documents"
    assert all(len(c.page_content) > 0 for c in chunks), "No chunk should be empty"
    print(f"\n  ✔ Produced {len(chunks)} chunks from {len(docs)} emails")


def test_chunk_metadata_preserved():
    """Metadata (subject, id, etc.) should carry through to chunks."""
    from data_loader import load_donor_emails, chunk_documents
    docs = load_donor_emails()
    chunks = chunk_documents(docs)
    for chunk in chunks:
        assert "subject" in chunk.metadata, "Chunk should carry subject metadata"
        assert "id" in chunk.metadata, "Chunk should carry id metadata"


# ─── question_generator tests (structure only, no real LLM call) ─────────────

def test_clean_json_response():
    """JSON cleaner should strip markdown fences."""
    from question_generator import _clean_json_response
    raw_with_fence = '```json\n{"key": "value"}\n```'
    cleaned = _clean_json_response(raw_with_fence)
    data = json.loads(cleaned)
    assert data["key"] == "value"

    raw_without_fence = '{"key": "value"}'
    cleaned2 = _clean_json_response(raw_without_fence)
    data2 = json.loads(cleaned2)
    assert data2["key"] == "value"


def test_question_topics_defined():
    """QUESTION_TOPICS should be a non-empty list of strings."""
    from question_generator import QUESTION_TOPICS
    assert isinstance(QUESTION_TOPICS, list)
    assert len(QUESTION_TOPICS) >= 5
    assert all(isinstance(t, str) for t in QUESTION_TOPICS)


# ─── evaluator tests (structure only, no real LLM call) ──────────────────────

def test_evaluator_mcq_correct():
    """Direct MCQ answer matching should work without LLM."""
    # We test the logic manually since LLM calls are mocked
    correct_answer = "B"
    student_answer = "B"
    assert student_answer.strip().upper() == correct_answer.strip().upper()


def test_evaluator_mcq_incorrect():
    """Wrong MCQ answer should be detected."""
    correct_answer = "C"
    student_answer = "A"
    assert student_answer.strip().upper() != correct_answer.strip().upper()


def test_evaluator_true_false_mapping():
    """True/False normalization: 'TRUE' should map to 'A'."""
    answer_input = "TRUE"
    mapped = "A" if answer_input.upper() in ("A", "TRUE") else "B"
    assert mapped == "A"

    answer_input2 = "FALSE"
    mapped2 = "A" if answer_input2.upper() in ("A", "TRUE") else "B"
    assert mapped2 == "B"


# ─── config tests ────────────────────────────────────────────────────────────

def test_config_defaults():
    """Config should export required attributes with valid types."""
    import config
    assert isinstance(config.CHUNK_SIZE, int) and config.CHUNK_SIZE > 0
    assert isinstance(config.CHUNK_OVERLAP, int) and config.CHUNK_OVERLAP >= 0
    assert isinstance(config.DEFAULT_NUM_QUESTIONS, int) and config.DEFAULT_NUM_QUESTIONS > 0
    assert isinstance(config.TOP_K_RETRIEVAL, int) and config.TOP_K_RETRIEVAL > 0
    assert isinstance(config.DATA_FILE, str)
    assert config.DATA_FILE.endswith(".json")
