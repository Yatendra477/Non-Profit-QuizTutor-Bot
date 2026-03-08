"""
evaluator.py — Evaluates user answers using Gemini LLM.
Provides RAG-powered contextual explanations for incorrect answers.
Uses the new google-genai SDK.
"""
import time
from typing import Dict, Any

from google import genai

from vector_store import similarity_search
import config

client = genai.Client(api_key=config.GOOGLE_API_KEY)


def _call_with_retry(prompt: str, max_retries: int = 4) -> str:
    """Calls Gemini with exponential backoff on 429 rate-limit errors."""
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
                    print(f"  Rate limit hit — waiting {delay}s...")
                    time.sleep(delay)
                    delay = min(delay * 2, 120)
                else:
                    raise
            else:
                raise
    raise RuntimeError("Max retries exceeded")

EVAL_PROMPT_SHORT_ANSWER = """You are a non-profit education tutor evaluating a student's quiz answer.

QUESTION: {question}
MODEL ANSWER: {correct_answer}
STUDENT'S ANSWER: {student_answer}

Evaluate whether the student's answer captures the essential meaning of the model answer.
Reply ONLY with "CORRECT" or "INCORRECT" (one word, no punctuation). Be generous — partial credit
counts as CORRECT if the core concept is captured."""

EXPLANATION_PROMPT = """You are a knowledgeable and encouraging non-profit education tutor.

A student answered a quiz question INCORRECTLY. Your job is to explain why their answer was wrong,
provide the correct answer with reasoning, and connect it to the broader non-profit domain context.

QUESTION: {question}
CORRECT ANSWER: {correct_answer}
STUDENT'S ANSWER: {student_answer}

RELEVANT CONTEXT FROM DONOR EMAILS:
{context}

Write a clear, educational explanation (3-5 sentences). Be encouraging and constructive.
Reference specific details from the context to make the explanation concrete and memorable.
Do NOT start with phrases like "I" — start directly with the explanation content."""

REINFORCEMENT_PROMPT = """You are an enthusiastic non-profit education tutor.
The student answered correctly! Write a brief (1-2 sentence) positive reinforcement message
that confirms their answer and adds one interesting related fact from the non-profit domain.

QUESTION: {question}
CORRECT ANSWER: {correct_answer}

Be warm, specific, and encouraging. Do NOT start with "I"."""


def evaluate_answer(question: Dict[str, Any], student_answer: str) -> Dict[str, Any]:
    """
    Evaluates the student's answer against the correct answer.

    Returns:
        {
            "is_correct": bool,
            "correct_answer": str,
            "explanation": str,
            "source_subjects": list[str]
        }
    """
    q_type = question.get("type", "mcq")
    correct_answer = question.get("answer", "")
    q_text = question.get("question", "")

    # --- Step 1: Determine correctness ---
    if q_type in ("mcq", "true_false"):
        is_correct = student_answer.strip().upper() == correct_answer.strip().upper()
    else:
        eval_prompt = EVAL_PROMPT_SHORT_ANSWER.format(
            question=q_text,
            correct_answer=correct_answer,
            student_answer=student_answer,
        )
        verdict = _call_with_retry(eval_prompt).strip().upper()
        is_correct = verdict.startswith("CORRECT")

    # --- Step 2: Get display value of the correct answer ---
    options = question.get("options", {})
    if options and correct_answer in options:
        correct_display = f"{correct_answer}. {options[correct_answer]}"
    else:
        correct_display = correct_answer

    # --- Step 3: Generate feedback ---
    if is_correct:
        feedback_prompt = REINFORCEMENT_PROMPT.format(
            question=q_text,
            correct_answer=correct_display,
        )
        explanation = _call_with_retry(feedback_prompt).strip()
        source_subjects = []
    else:
        context_docs = similarity_search(
            query=q_text + " " + question.get("topic", ""),
            k=config.TOP_K_RETRIEVAL,
        )
        context = "\n\n---\n\n".join([doc.page_content for doc in context_docs])
        source_subjects = [doc.metadata.get("subject", "Unknown") for doc in context_docs]

        explanation_prompt = EXPLANATION_PROMPT.format(
            question=q_text,
            correct_answer=correct_display,
            student_answer=student_answer,
            context=context,
        )
        explanation = _call_with_retry(explanation_prompt).strip()

    return {
        "is_correct": is_correct,
        "correct_answer": correct_display,
        "explanation": explanation,
        "source_subjects": source_subjects,
    }
