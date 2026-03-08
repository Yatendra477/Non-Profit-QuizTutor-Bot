"""
ingest.py — Ingestion pipeline: load emails → chunk → embed → store in ChromaDB.
Run this once before starting the quiz bot.
"""
from rich.console import Console
from rich.progress import track

from data_loader import load_donor_emails, chunk_documents
from vector_store import build_vector_store

console = Console()


def run_ingestion():
    console.print("\n[bold cyan]━━━ Non-Profit Quiz Bot — Data Ingestion ━━━[/bold cyan]\n")

    # Step 1: Load emails
    console.print("[yellow]📂 Loading donor emails...[/yellow]")
    documents = load_donor_emails()
    console.print(f"[green]✔ Loaded {len(documents)} emails.[/green]")

    # Step 2: Chunk documents
    console.print("[yellow]✂  Splitting into chunks...[/yellow]")
    chunks = chunk_documents(documents)
    console.print(f"[green]✔ Created {len(chunks)} text chunks.[/green]")

    # Step 3: Embed and store
    console.print("[yellow]🧠 Embedding and storing in ChromaDB...[/yellow]")
    console.print("[dim](This may take a few seconds on first run)[/dim]")
    build_vector_store(chunks)

    console.print(
        "\n[bold green]✅ Ingestion complete![/bold green] "
        "Vector database is ready.\n"
        "You can now run: [bold]python main.py --quiz[/bold]\n"
    )


if __name__ == "__main__":
    run_ingestion()
