# 🎓 Non-Profit Quiz/Tutor Bot

An interactive AI-driven educational bot for the **Non-Profit domain**. It quizzes users on real donor email content, evaluates answers semantically using **Google Gemini**, and explains wrong answers with **RAG-powered context** drawn directly from the knowledge base.

---

## ✨ Features

| Feature | Details |
|---|---|
| **3 Question Types** | Multiple Choice, True/False, Short Answer |
| **RAG Explanations** | Wrong answers trigger context-aware explanations from donor emails |
| **Semantic Evaluation** | Short answers evaluated by LLM — not just string matching |
| **Hint System** | Press `H` on any MCQ/T-F question for a hint |
| **Score Dashboard** | Final results table with per-topic breakdown and study suggestions |
| **Rich CLI** | Styled terminal interface with colours, panels, and tables |

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Your API Key

```bash
# Windows (PowerShell)
copy .env.example .env
# Then open .env and add your key:
# GOOGLE_API_KEY=your_key_here
```

> Get a free Gemini API key at: https://aistudio.google.com/app/apikey

### 3. Ingest Donor Emails (run once)

```bash
python main.py --ingest
```

This loads the 15 sample donor emails into a local ChromaDB vector database.

### 4. Start the Quiz

```bash
python main.py
# or
python main.py --quiz --num-questions 5
```

---

## 🏗️ Project Structure

```
Non-Profit QuizTutor Bot/
├── data/
│   └── donor_emails.json       # 15 curated sample donor emails (knowledge base)
├── chroma_db/                  # Created on first ingest (auto-generated)
├── config.py                   # All settings (models, paths, chunk sizes)
├── data_loader.py              # Load & chunk donor emails
├── vector_store.py             # ChromaDB embed + retrieve
├── ingest.py                   # Ingestion pipeline entry point
├── question_generator.py       # LLM-based MCQ / T-F / Short Answer generator
├── evaluator.py                # Answer evaluation + RAG explanation engine
├── bot.py                      # Interactive CLI session manager
├── main.py                     # ← Run this
├── test_smoke.py               # Pytest smoke tests
├── requirements.txt
└── .env.example
```

---

## 🧪 Running Tests

```bash
python -m pytest test_smoke.py -v
```

Tests cover: data loading, chunking, metadata preservation, JSON parsing, evaluation logic, and config validation — **no API key required**.

---

## ⚙️ Configuration (`config.py`)

| Setting | Default | Description |
|---|---|---|
| `LLM_MODEL` | `gemini-1.5-flash` | Gemini model for Q generation & evaluation |
| `EMBEDDING_MODEL` | `models/embedding-001` | Gemini embedding model |
| `CHUNK_SIZE` | `500` | Characters per text chunk |
| `CHUNK_OVERLAP` | `80` | Overlap between chunks |
| `DEFAULT_NUM_QUESTIONS` | `5` | Questions per quiz session |
| `TOP_K_RETRIEVAL` | `3` | Chunks retrieved for RAG context |

---

## 🔄 How It Works

```
Donor Emails (JSON)
      │
      ▼
 [ingest.py] → ChromaDB Vector Store
                      │
      ┌───────────────┘
      ▼
 [question_generator.py] → Quiz Questions (MCQ / T-F / Short Answer)
      │
      ▼
 [bot.py / main.py] → Interactive CLI Session
      │
 User Answer
      │
      ▼
 [evaluator.py] ← RAG Context from ChromaDB
      │
      ▼
 Score + Contextual Explanation
```
