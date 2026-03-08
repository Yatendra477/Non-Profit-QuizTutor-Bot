"""
main.py — Entry point for the Non-Profit Quiz/Tutor Bot.

Usage:
    python main.py --ingest                   # Ingest donor emails into ChromaDB
    python main.py --quiz                     # Start a quiz session (default)
    python main.py --quiz --num-questions 10  # Quiz with 10 questions
    python main.py --tutor                    # Start the Writing Tutor mode
    python main.py                            # Shows mode selection menu
"""
import argparse
import sys

from rich.console import Console
from rich.prompt import Prompt

console = Console()


def check_api_key():
    """Validates that GOOGLE_API_KEY is set before proceeding."""
    import config
    if not config.GOOGLE_API_KEY or config.GOOGLE_API_KEY == "your_gemini_api_key_here":
        console.print(
            "\n[bold red]❌ Error:[/bold red] GOOGLE_API_KEY is not set.\n\n"
            "  1. Copy [bold].env.example[/bold] to [bold].env[/bold]\n"
            "  2. Add your Gemini API key from [link]https://aistudio.google.com/app/apikey[/link]\n"
            "  3. Run again\n"
        )
        sys.exit(1)


def run_ingest():
    from ingest import run_ingestion
    run_ingestion()


def ensure_vector_db():
    """Auto-ingests if the vector DB is missing."""
    import os
    import config
    if not os.path.exists(config.CHROMA_DB_PATH):
        console.print(
            "\n[bold yellow]⚠  Vector database not found.[/bold yellow]\n"
            "Running ingestion first...\n"
        )
        run_ingest()


def run_quiz(num_questions: int):
    ensure_vector_db()

    console.print(
        f"\n[cyan]🧠 Generating [bold]{num_questions} questions[/bold]... "
        f"(this may take ~15-30 seconds)[/cyan]\n"
    )

    from question_generator import generate_quiz
    from bot import run_quiz_session

    questions = generate_quiz(num_questions=num_questions)

    if not questions:
        console.print("[bold red]❌ No questions could be generated. Check your API key and try again.[/bold red]")
        sys.exit(1)

    run_quiz_session(questions)


def run_tutor():
    ensure_vector_db()
    from writing_tutor import run_writing_tutor
    run_writing_tutor()


def show_mode_menu() -> str:
    """Interactive mode selector shown when no flags are passed."""
    console.print()
    console.print("[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold cyan]")
    console.print("[bold cyan]     🎓  Non-Profit AI Learning Bot  🎓[/bold cyan]")
    console.print("[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold cyan]\n")
    console.print("  [bold cyan]1[/bold cyan]. 📝  Quiz Mode     — Answer questions on donor email topics")
    console.print("  [bold cyan]2[/bold cyan]. ✍️   Writing Tutor — Draft donor emails and get AI feedback")
    console.print("  [bold cyan]3[/bold cyan]. 📥  Re-Ingest     — Reload emails into the vector database\n")

    choice = Prompt.ask("  [bold]Select mode[/bold] [1/2/3]", default="1").strip()
    return choice


def main():
    parser = argparse.ArgumentParser(
        description="Non-Profit AI Learning Bot — Powered by Google Gemini + RAG",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                            # Interactive mode selector
  python main.py --ingest                   # Load emails into vector DB (run once)
  python main.py --quiz                     # Default 5-question quiz
  python main.py --quiz --num-questions 10  # 10-question quiz
  python main.py --tutor                    # Writing Tutor mode
        """,
    )
    parser.add_argument(
        "--ingest",
        action="store_true",
        help="Run the data ingestion pipeline (loads donor emails into ChromaDB)",
    )
    parser.add_argument(
        "--quiz",
        action="store_true",
        help="Start an interactive quiz session",
    )
    parser.add_argument(
        "--tutor",
        action="store_true",
        help="Start the Writing Tutor mode (draft donor emails + get AI feedback)",
    )
    parser.add_argument(
        "--num-questions",
        type=int,
        default=5,
        metavar="N",
        help="Number of quiz questions to generate (default: 5, used with --quiz)",
    )

    args = parser.parse_args()
    check_api_key()

    if args.ingest:
        run_ingest()
    elif args.quiz:
        run_quiz(num_questions=args.num_questions)
    elif args.tutor:
        run_tutor()
    else:
        # No flag: show interactive menu
        choice = show_mode_menu()
        if choice == "1":
            run_quiz(num_questions=args.num_questions)
        elif choice == "2":
            run_tutor()
        elif choice == "3":
            run_ingest()
        else:
            console.print("[yellow]Invalid choice. Starting Quiz Mode by default.[/yellow]")
            run_quiz(num_questions=args.num_questions)


if __name__ == "__main__":
    main()
