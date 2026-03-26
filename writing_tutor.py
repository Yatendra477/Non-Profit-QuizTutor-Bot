"""
writing_tutor.py — Writing Tutor mode for the Non-Profit Quiz/Tutor Bot.

Presents the user with a donor email writing scenario, accepts their draft,
retrieves RAG context from ChromaDB, and evaluates their email using Groq LLM
with the structured evaluation prompt. Returns JSON feedback displayed in the CLI.
"""
import json
import time
from typing import Dict, Any

from groq import Groq, RateLimitError
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.rule import Rule
from rich.prompt import Prompt
from rich import box

from vector_store import similarity_search
import config

console = Console()
client = Groq(api_key=config.GROQ_API_KEY)

# ─── Predefined Writing Scenarios ─────────────────────────────────────────────
SCENARIOS = [
    {
        "id": 1,
        "title": "First-Time Donor Thank-You",
        "description": (
            "A first-time donor named Rachel Kim just made a $150 donation to your organization, "
            "'Bright Futures Foundation', which provides after-school tutoring to low-income students. "
            "Write a thank-you email to Rachel that acknowledges her gift, explains the impact, "
            "informs her of any tax-deductibility, and makes her feel genuinely appreciated. "
            "Your organization's EIN is 82-3456789."
        ),
        "search_query": "donor acknowledgment tax receipt 501c3 thank you donation impact",
    },
    {
        "id": 2,
        "title": "Year-End Matching Gift Appeal",
        "description": (
            "Your organization, 'Clean Water Now', is running a year-end campaign. A board member "
            "has pledged to match all gifts up to $20,000, but only until December 31. "
            "You have raised $12,000 so far and need $8,000 more. "
            "Write a fundraising appeal email to your donor list that creates urgency, "
            "explains the matching gift opportunity, and includes a clear call to action. "
            "The deadline is in 5 days."
        ),
        "search_query": "matching gift year-end fundraising campaign urgency call to action deadline",
    },
    {
        "id": 3,
        "title": "Lapsed Donor Re-Engagement",
        "description": (
            "A donor named Thomas Webb gave $500 last year but has not donated this year. "
            "Your organization, 'Second Harvest Food Bank', wants to re-engage him. "
            "Write a re-engagement email that acknowledges his past support, shares a recent "
            "impact story, and invites him to renew his support — without sounding pushy or "
            "making him feel guilty for not giving sooner."
        ),
        "search_query": "recurring donor stewardship impact report donor retention re-engagement",
    },
    {
        "id": 4,
        "title": "Volunteer Appreciation and Recruitment",
        "description": (
            "Your organization, 'Literacy Bridge', is running low on tutoring volunteers. "
            "Write an email to your existing volunteer and donor list that: "
            "(1) thanks current volunteers for their service, "
            "(2) shares a specific impact metric, and "
            "(3) makes a targeted ask for new volunteer sign-ups with clear commitment details — "
            "including how many hours per week are needed and the minimum time commitment."
        ),
        "search_query": "volunteer orientation commitment hours minimum term appreciation recruitment",
    },
    {
        "id": 5,
        "title": "Grant Reporting Reminder to Grantee",
        "description": (
            "Your foundation just awarded a $30,000 grant to a partner organization. "
            "Write a formal email reminding the grantee organization of their reporting requirements, "
            "the reporting schedule, what happens if reports are late, and when the second "
            "installment of funds will be released."
        ),
        "search_query": "grant reporting requirements quarterly report installment disbursement compliance",
    },
    {
        "id": 6,
        "title": "Planned Giving Introduction",
        "description": (
            "A long-time major donor, Eleanor Davis (age 68), has expressed interest in "
            "leaving a legacy gift. Write a warm, respectful email from your organization "
            "'Arts & Culture Alliance' introducing her to planned giving options (bequests, "
            "beneficiary designations, etc.), the benefits of joining your legacy society, "
            "and who she can contact to discuss further. "
            "Do NOT use any legal or financial jargon without explaining it."
        ),
        "search_query": "planned giving bequest legacy estate charitable trust gift annuity",
    },
]

# ─── Evaluation Prompt ────────────────────────────────────────────────────────
EVALUATION_PROMPT = """You are an expert Non-Profit Communications Director and an empathetic, highly skilled tutor. Your goal is to train non-profit staff on how to write highly effective, ethical, and engaging emails to donors.

You will be provided with three pieces of information:
1. CONTEXT: Best practices and guidelines retrieved from our non-profit communication knowledge base.
2. SCENARIO: The specific situation the user was asked to respond to.
3. USER ANSWER: The email drafted by the trainee/user.

Your task is to evaluate the USER ANSWER based strictly on the provided CONTEXT.

### Evaluation Criteria:
- Tone: Is it empathetic, grateful, and aligned with non-profit values?
- Clarity & Action: Is the message clear, and is the call-to-action appropriate?
- Compliance: Did they follow the specific rules outlined in the CONTEXT?

### Constraints:
- Be constructive and encouraging in your feedback. Address the user directly as "you".
- If the user's answer violates a rule in the CONTEXT, explicitly point out which rule was missed.
- Do not make up non-profit rules that are not present in the CONTEXT.

=========================================
CONTEXT:
{retrieved_vector_db_context}

SCENARIO:
{scenario_description}

USER ANSWER:
{user_drafted_email}
=========================================

Provide your evaluation strictly as a valid JSON object using the following structure. Do not include markdown formatting like ```json or any conversational text outside the JSON object.

{{
  "score_out_of_10": <integer>,
  "what_worked_well": "<string detailing the strengths of their draft>",
  "areas_for_improvement": "<string detailing what they missed based on the CONTEXT>",
  "expert_rewrite": "<string providing a polished, perfect version of the email>",
  "core_lesson": "<a short, one-sentence takeaway rule for the user to remember>"
}}"""


def _call_with_retry(prompt: str, max_retries: int = 4) -> str:
    """Calls Groq with exponential backoff on rate-limit errors."""
    delay = 15
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content
        except RateLimitError:
            if attempt < max_retries - 1:
                console.print(f"  [dim]Rate limit — waiting {delay}s...[/dim]")
                time.sleep(delay)
                delay = min(delay * 2, 60)
            else:
                raise
        except Exception:
            raise
    raise RuntimeError("Max retries exceeded")


def _clean_json(text: str) -> str:
    text = text.strip()
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        return text[start:end+1]
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.startswith("```")]
        text = "\n".join(lines).strip()
    return text


def _collect_draft() -> str:
    """
    Collects a multi-line email draft from the user.
    They type lines and enter a blank line twice to finish.
    """
    console.print(
        "\n  [dim]Type your email draft below. Press [bold]Enter twice[/bold] on a blank line when done.[/dim]\n"
    )
    lines = []
    consecutive_blanks = 0
    while True:
        line = input("  ")
        if line == "":
            consecutive_blanks += 1
            if consecutive_blanks >= 2:
                break
            lines.append("")
        else:
            consecutive_blanks = 0
            lines.append(line)
    # Strip trailing blank lines
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def _display_scenario(scenario: Dict, index: int, total: int):
    """Renders the scenario card."""
    console.print()
    console.rule(
        f"[cyan] Scenario {index} of {total} | [bold]{scenario['title']}[/bold] [cyan]",
        style="cyan",
    )
    console.print()
    console.print(
        Panel(
            f"[white]{scenario['description']}[/white]",
            title="[bold]📋 Your Scenario[/bold]",
            border_style="cyan",
            padding=(1, 2),
        )
    )


def _display_feedback(result: Dict[str, Any], scenario_title: str):
    """Renders the evaluation feedback in a rich layout."""
    score = result.get("score_out_of_10", 0)
    console.print()
    console.rule("[cyan] ✦  Tutor Evaluation  ✦ [cyan]", style="cyan")
    console.print()

    # Score badge
    if score >= 8:
        score_color = "bold green"
        grade = "Excellent Work! 🏆"
    elif score >= 6:
        score_color = "bold yellow"
        grade = "Good Effort! 📚"
    else:
        score_color = "bold red"
        grade = "Needs Improvement 💪"

    console.print(
        Panel(
            f"[{score_color}]Score: {score} / 10   —   {grade}[/{score_color}]",
            title=f"[bold]{scenario_title}[/bold]",
            border_style="cyan",
            padding=(0, 2),
        )
    )

    # What worked well
    if result.get("what_worked_well"):
        console.print(
            Panel(
                f"[white]{result['what_worked_well']}[/white]",
                title="[bold green]✅ What Worked Well[/bold green]",
                border_style="green",
                padding=(0, 2),
            )
        )

    # Areas for improvement
    if result.get("areas_for_improvement"):
        console.print(
            Panel(
                f"[white]{result['areas_for_improvement']}[/white]",
                title="[bold yellow]💡 Areas for Improvement[/bold yellow]",
                border_style="yellow",
                padding=(0, 2),
            )
        )

    # Expert rewrite
    if result.get("expert_rewrite"):
        console.print(
            Panel(
                f"[white]{result['expert_rewrite']}[/white]",
                title="[bold cyan]✍️  Expert Rewrite[/bold cyan]",
                border_style="cyan",
                padding=(1, 2),
            )
        )

    # Core lesson
    if result.get("core_lesson"):
        console.print(
            Panel(
                f"[bold italic white]{result['core_lesson']}[/bold italic white]",
                title="[bold magenta]📌 Core Lesson to Remember[/bold magenta]",
                border_style="magenta",
                padding=(0, 2),
            )
        )

    console.print()


def _evaluate_draft(scenario: Dict, user_draft: str, vector_store=None) -> Dict[str, Any]:
    """Retrieves RAG context and evaluates the user's email draft."""
    # RAG: retrieve relevant context from donor emails
    k = config.TOP_K_RETRIEVAL
    if vector_store is not None:
        context_docs = vector_store.similarity_search(scenario["search_query"], k=k)
    else:
        context_docs = similarity_search(
            query=scenario["search_query"],
            k=k,
        )
    context = "\n\n---\n\n".join([doc.page_content for doc in context_docs])

    prompt = EVALUATION_PROMPT.format(
        retrieved_vector_db_context=context,
        scenario_description=scenario["description"],
        user_drafted_email=user_draft,
    )

    raw = _clean_json(_call_with_retry(prompt))
    try:
        return json.loads(raw, strict=False)
    except json.JSONDecodeError:
        return {
            "score_out_of_10": 0,
            "what_worked_well": "Could not parse evaluation. Please try again.",
            "areas_for_improvement": "",
            "expert_rewrite": "",
            "core_lesson": "",
        }


def _scenario_selector() -> Dict:
    """Lets the user pick a scenario or get a random one."""
    console.print("\n[bold cyan]━━━ Writing Tutor — Choose a Scenario ━━━[/bold cyan]\n")
    for s in SCENARIOS:
        console.print(f"  [bold cyan]{s['id']}[/bold cyan]. {s['title']}")

    console.print(f"  [bold cyan]R[/bold cyan]. Random scenario\n")

    while True:
        choice = Prompt.ask("  [bold]Select scenario[/bold]").strip().upper()
        if choice == "R":
            import random
            return random.choice(SCENARIOS)
        try:
            num = int(choice)
            match = next((s for s in SCENARIOS if s["id"] == num), None)
            if match:
                return match
        except ValueError:
            pass
        console.print("  [yellow]⚠ Please enter a number 1–6 or R[/yellow]")


def run_writing_tutor():
    """
    Runs the full writing tutor session.
    - User selects a scenario
    - User types their email draft
    - Bot evaluates with RAG + LLM and displays rich feedback
    """
    console.print("\n[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold cyan]")
    console.print("[bold cyan]   ✍️   Non-Profit Writing Tutor Mode   ✍️[/bold cyan]")
    console.print("[bold cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold cyan]")
    console.print(
        "\n[white]You will be given a real-world non-profit email scenario.\n"
        "Draft your best response, then receive expert AI feedback\n"
        "grounded in actual non-profit communication best practices.[/white]\n"
    )

    scores = []
    session_active = True

    while session_active:
        scenario = _scenario_selector()
        _display_scenario(scenario, index=1, total=1)

        user_draft = _collect_draft()

        if not user_draft.strip():
            console.print("  [yellow]⚠ No draft entered. Skipping evaluation.[/yellow]")
        else:
            console.print(
                "\n  [dim]⏳ Evaluating your draft with RAG + Groq AI...[/dim]"
            )
            result = _evaluate_draft(scenario, user_draft)
            _display_feedback(result, scenario["title"])
            scores.append(result.get("score_out_of_10", 0))

        again = Prompt.ask(
            "\n  [bold]Try another scenario?[/bold] [Y/N]",
            default="N",
        ).strip().upper()
        if again != "Y":
            session_active = False

    # Session summary
    if scores:
        avg = sum(scores) / len(scores)
        console.print(
            Panel(
                f"[white]Scenarios completed: [bold]{len(scores)}[/bold]\n"
                f"Average score: [bold]{avg:.1f} / 10[/bold][/white]",
                title="[bold cyan]📊 Session Summary[/bold cyan]",
                border_style="cyan",
                padding=(0, 2),
            )
        )

    console.print("\n[dim]Thank you for using the Non-Profit Writing Tutor. Keep practising! ✍️[/dim]\n")
