"""
bot.py — Interactive CLI quiz session manager for the Non-Profit Quiz/Tutor Bot.
Uses Rich for premium terminal formatting.
"""
import time
from typing import List, Dict, Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt
from rich.rule import Rule
from rich import box

from evaluator import evaluate_answer
import config

console = Console()

# ─── ANSI/Rich colour palette ─────────────────────────────────────────────────
BRAND_COLOR = "cyan"
CORRECT_COLOR = "bold green"
WRONG_COLOR = "bold red"
WARN_COLOR = "yellow"
DIM_COLOR = "dim"
TOPIC_COLOR = "magenta"

BANNER = r"""
 _   _             ____            _____ _ _   _____      _
| \ | | ___  _ __ |  _ \ _ __ ___|_   _(_) |_| ____|__ _| |_ ___
|  \| |/ _ \| '_ \| |_) | '__/ _ \| | | | __| _|  / _` | __/ __|
| |\  | (_) | | | |  __/| | | (_) | | | | |_| |__| (_| | |_\__ \
|_| \_|\___/|_| |_|_|   |_|  \___/|_| |_|\__|_____\__,_|\__|___/

          ✦  Non-Profit Quiz & Tutor Bot  ✦
"""


def _header():
    console.print(f"[bold {BRAND_COLOR}]{BANNER}[/bold {BRAND_COLOR}]")
    console.print(
        Panel(
            "[white]Test your knowledge of the [bold]Non-Profit domain[/bold] — "
            "donor relations, grant management, fundraising, and more.[/white]\n"
            "[dim]Powered by Google Gemini AI + Retrieval-Augmented Generation (RAG)[/dim]",
            border_style=BRAND_COLOR,
            padding=(0, 2),
        )
    )


def _display_question(index: int, total: int, question: Dict[str, Any]):
    """Renders a formatted question card in the terminal."""
    console.print()
    console.rule(
        f"[{BRAND_COLOR}] Question {index} of {total} "
        f"| Topic: [{TOPIC_COLOR}]{question.get('topic', '').title()}[/{TOPIC_COLOR}] "
        f"| Difficulty: [yellow]{question.get('difficulty', '').upper()}[/yellow] [{BRAND_COLOR}]",
        style=BRAND_COLOR,
    )
    console.print()

    q_type = question.get("type", "mcq")
    console.print(f"  [bold white]{question['question']}[/bold white]\n")

    options = question.get("options", {})
    if options:
        for key, val in options.items():
            console.print(f"    [bold {BRAND_COLOR}]{key}[/bold {BRAND_COLOR}]  {val}")
        console.print()


def _get_answer(question: Dict[str, Any]) -> str:
    """Prompts the user for an answer, appropriate to the question type."""
    q_type = question.get("type", "mcq")

    if q_type == "mcq":
        valid = list(question.get("options", {}).keys())  # ['A','B','C','D']
        while True:
            answer = Prompt.ask(
                f"  [bold]Your answer[/bold] [{'/'.join(valid)}]"
            ).strip().upper()
            if answer in valid:
                return answer
            console.print(f"  [{WARN_COLOR}]⚠  Please enter one of: {', '.join(valid)}[/{WARN_COLOR}]")

    elif q_type == "true_false":
        while True:
            answer = Prompt.ask("  [bold]Your answer[/bold] [A=True / B=False]").strip().upper()
            if answer in ("A", "B", "TRUE", "FALSE"):
                return "A" if answer in ("A", "TRUE") else "B"
            console.print(f"  [{WARN_COLOR}]⚠  Please enter A (True) or B (False)[/{WARN_COLOR}]")

    else:  # short_answer
        answer = Prompt.ask("  [bold]Your answer[/bold]").strip()
        return answer


def _display_result(result: Dict[str, Any], question: Dict[str, Any]):
    """Displays colour-coded evaluation result and explanation."""
    console.print()

    if result["is_correct"]:
        icon = "✅"
        color = CORRECT_COLOR
        header = f"{icon}  [bold green]Correct![/bold green]"
    else:
        icon = "❌"
        color = WRONG_COLOR
        header = (
            f"{icon}  [bold red]Incorrect.[/bold red]  "
            f"Correct answer: [{BRAND_COLOR}]{result['correct_answer']}[/{BRAND_COLOR}]"
        )

    console.print(Panel(header, border_style="green" if result["is_correct"] else "red", padding=(0, 2)))

    # Explanation / reinforcement
    console.print(
        Panel(
            f"[white]{result['explanation']}[/white]",
            title="[bold]Tutor Insight[/bold]",
            border_style=BRAND_COLOR,
            padding=(0, 2),
        )
    )

    # Show source emails used for RAG explanation (wrong answers only)
    sources = result.get("source_subjects", [])
    if sources and not result["is_correct"]:
        src_text = "\n".join(f"  • {s}" for s in sources)
        console.print(
            Panel(
                f"[dim]{src_text}[/dim]",
                title="[dim]📧 Referenced Donor Emails[/dim]",
                border_style="dim",
                padding=(0, 2),
            )
        )


def _display_hint(question: Dict[str, Any]):
    """Shows a hint for the current question."""
    hint = question.get("hint", "")
    if hint:
        console.print(f"\n  [{WARN_COLOR}]💡 Hint: {hint}[/{WARN_COLOR}]\n")
    else:
        console.print(f"  [{WARN_COLOR}]No hint available for this question.[/{WARN_COLOR}]\n")


def _final_report(questions: List[Dict], results: List[Dict]):
    """Renders the final score summary table."""
    console.print()
    console.rule(f"[{BRAND_COLOR}] ✦  Quiz Complete — Your Results  ✦ [{BRAND_COLOR}]", style=BRAND_COLOR)
    console.print()

    total = len(results)
    correct = sum(1 for r in results if r["is_correct"])
    pct = (correct / total * 100) if total > 0 else 0

    # Score badge
    if pct >= 80:
        badge = "🏆 Excellent!"
        badge_color = "bold green"
    elif pct >= 60:
        badge = "📚 Good effort!"
        badge_color = "bold yellow"
    else:
        badge = "💪 Keep learning!"
        badge_color = "bold red"

    console.print(
        Panel(
            f"[bold white]Score: {correct}/{total}  ({pct:.0f}%)[/bold white]\n"
            f"[{badge_color}]{badge}[/{badge_color}]",
            border_style=BRAND_COLOR,
            padding=(1, 4),
        )
    )

    # Per-question breakdown table
    table = Table(
        title="Question Breakdown",
        box=box.ROUNDED,
        border_style=BRAND_COLOR,
        show_lines=True,
    )
    table.add_column("#", style="dim", width=3, justify="center")
    table.add_column("Topic", style="magenta")
    table.add_column("Type", style="cyan", width=12)
    table.add_column("Difficulty", width=10)
    table.add_column("Result", justify="center", width=10)

    diff_colors = {"easy": "green", "medium": "yellow", "hard": "red"}

    for i, (q, r) in enumerate(zip(questions, results), 1):
        diff = q.get("difficulty", "")
        table.add_row(
            str(i),
            q.get("topic", "").replace("_", " ").title(),
            q.get("type", "").replace("_", " ").title(),
            f"[{diff_colors.get(diff, 'white')}]{diff.upper()}[/{diff_colors.get(diff, 'white')}]",
            "✅" if r["is_correct"] else "❌",
        )

    console.print(table)
    console.print()

    # Missed topics summary
    missed = [q.get("topic", "") for q, r in zip(questions, results) if not r["is_correct"]]
    if missed:
        console.print(
            Panel(
                "[white]Review these areas:\n" + "\n".join(f"  • {t.replace('_',' ').title()}" for t in missed),
                title="[bold yellow]📖 Suggested Study Topics[/bold yellow]",
                border_style="yellow",
                padding=(0, 2),
            )
        )

    console.print(f"\n[dim]Thank you for using the Non-Profit Quiz Bot. Keep learning! 🌟[/dim]\n")


def run_quiz_session(questions: List[Dict[str, Any]]):
    """
    Runs the full interactive quiz session.
    
    Args:
        questions: Pre-generated list of question dicts from question_generator.
    """
    _header()

    total = len(questions)
    console.print(
        f"\n[{BRAND_COLOR}]Starting a [bold]{total}-question quiz[/bold] on the Non-Profit domain...[/{BRAND_COLOR}]"
        f"\n[dim]Type your answer when prompted. Enter 'H' before answering to reveal a hint.[/dim]\n"
    )

    Prompt.ask("  Press [Enter] to begin", default="")

    results = []

    for i, question in enumerate(questions, 1):
        _display_question(i, total, question)

        # Hint check for MCQ and True/False
        q_type = question.get("type", "mcq")
        if q_type in ("mcq", "true_false"):
            options = list(question.get("options", {}).keys())
            hint_trigger = Prompt.ask(
                f"  [dim]Enter your answer or[/dim] [bold]H[/bold] [dim]for a hint[/dim] [{'/'.join(options)}/H]",
                default=""
            ).strip().upper()

            if hint_trigger == "H":
                _display_hint(question)
                answer = _get_answer(question)
            elif hint_trigger in options:
                answer = hint_trigger
            else:
                answer = _get_answer(question)
        else:
            answer = _get_answer(question)

        # Evaluate
        console.print(f"\n  [dim]⏳ Evaluating your answer...[/dim]")
        result = evaluate_answer(question, answer)
        results.append(result)

        _display_result(result, question)

        if i < total:
            Prompt.ask("\n  [dim]Press Enter for the next question[/dim]", default="")

    _final_report(questions, results)
