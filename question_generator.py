"""
question_generator.py — Generates quiz questions from donor email content using Gemini LLM.
Uses a SINGLE batch API call to generate all questions at once — minimises API quota usage.
"""
import json
import random
import time
from typing import List, Dict, Any

from google import genai

from vector_store import similarity_search
import config

# Configure new google-genai client
client = genai.Client(api_key=config.GOOGLE_API_KEY)

QUESTION_TOPICS = [
    "grant funding requirements",
    "donor acknowledgment and tax receipts",
    "fundraising campaign strategies",
    "volunteer management",
    "nonprofit financial stewardship",
    "board governance",
    "planned giving and legacy donations",
    "matching gift programs",
    "recurring donor programs",
    "disaster relief and emergency appeals",
]

DIFFICULTIES = ["easy", "medium", "hard"]

BATCH_PROMPT = """You are an expert quiz creator for non-profit education.
Based on the following excerpts from donor emails, generate exactly {num_questions} quiz questions.

CONTEXT FROM DONOR EMAILS:
{context}

QUESTION SPECIFICATIONS:
{specs}

RULES:
- Every question must be directly answerable from the context provided.
- For MCQ: provide exactly 4 options labeled A, B, C, D. Only one is correct.
- For true_false: options must be exactly {{"A": "True", "B": "False"}}.
- For short_answer: options must be {{}}.  Provide a model answer string.
- Vary the correct answers — don't always pick A.
- The "hint" must NOT reveal the answer.

Respond ONLY with a valid JSON array (no markdown, no extra text) in this format:
[
  {{
    "type": "mcq",
    "question": "...",
    "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
    "answer": "B",
    "topic": "...",
    "difficulty": "easy",
    "hint": "..."
  }},
  ...
]"""


def _clean_json_response(text: str) -> str:
    """Strip markdown fences if the LLM wraps JSON in them."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.startswith("```")]
        text = "\n".join(lines).strip()
    return text


def _call_with_retry(prompt: str, max_retries: int = 4) -> str:
    """
    Calls the Gemini API with exponential backoff on 429 rate-limit errors.
    """
    delay = 30
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=config.LLM_MODEL,
                contents=prompt,
            )
            return response.text
        except Exception as e:
            err = str(e)
            if "429" in err or "RESOURCE_EXHAUSTED" in err or "retryDelay" in err:
                if attempt < max_retries - 1:
                    print(f"  Rate limit hit — waiting {delay}s before retry ({attempt + 1}/{max_retries - 1})...")
                    time.sleep(delay)
                    delay = min(delay * 2, 120)
                else:
                    raise
            else:
                raise
    raise RuntimeError("Max retries exceeded")


def generate_quiz(num_questions: int = config.DEFAULT_NUM_QUESTIONS) -> List[Dict[str, Any]]:
    """
    Generates a balanced quiz in a SINGLE LLM call to minimise API quota usage.
    Returns a list of question dicts.
    """
    # Pick random topics and a balanced mix of types/difficulties
    q_types = ["mcq", "mcq", "true_false", "true_false", "short_answer"]
    shuffled_topics = random.sample(QUESTION_TOPICS, min(num_questions, len(QUESTION_TOPICS)))

    specs_lines = []
    for i in range(num_questions):
        q_type = q_types[i % len(q_types)]
        topic = shuffled_topics[i % len(shuffled_topics)]
        difficulty = DIFFICULTIES[i % len(DIFFICULTIES)]
        specs_lines.append(
            f"  Question {i + 1}: type={q_type}, topic=\"{topic}\", difficulty={difficulty}"
        )
    specs = "\n".join(specs_lines)

    # Gather broad context from multiple topics for richer material
    all_topics_query = " ".join(shuffled_topics[:3])
    context_docs = similarity_search(all_topics_query, k=min(6, config.TOP_K_RETRIEVAL * 2))
    context = "\n\n---\n\n".join([doc.page_content for doc in context_docs])

    prompt = BATCH_PROMPT.format(
        num_questions=num_questions,
        context=context,
        specs=specs,
    )

    raw = _clean_json_response(_call_with_retry(prompt))

    try:
        questions = json.loads(raw)
        # Ensure it's a list
        if not isinstance(questions, list):
            questions = [questions]
        # Attach source metadata
        source_subjects = [doc.metadata.get("subject", "Unknown") for doc in context_docs]
        for q in questions:
            q["context_sources"] = source_subjects
        return questions
    except (json.JSONDecodeError, TypeError):
        print("  Warning: Could not parse batch response. Returning empty quiz.")
        return []
