from rich.console import Console
from rich.prompt import Prompt
import json
from database.connection import SessionLocal, init_db
from database.models import Idea
from llm.matcher import ConceptMatcher
from scheduler.runner import DailyRunner

console = Console()

def onboarding():
    console.print("\n[bold cyan]🚀 Idea Validator - Let's check if your idea already exists![/bold cyan]\n")

    user_idea = Prompt.ask("[green]Describe your invention idea in detail[/green]")

    console.print("\n[yellow]🤖 Analyzing your idea with AI...[/yellow]")

    # Extract concepts
    matcher = ConceptMatcher()
    concepts = matcher.extract_concepts(user_idea)

    console.print(f"\n[cyan]Core Function:[/cyan] {concepts.get('core_function')}")
    console.print(f"[cyan]Key Features:[/cyan] {concepts.get('key_features')}")
    console.print(f"[cyan]Search Keywords:[/cyan] {', '.join(concepts.get('search_keywords', []))}")

    confirm = Prompt.ask("\n[yellow]Does this look right?[/yellow]", choices=["yes", "no"], default="yes")

    if confirm == "no":
        console.print("[red]Exiting - please refine your description and try again[/red]")
        return

    # Save to database
    db = SessionLocal()
    idea = Idea(
        user_description=user_idea,
        extracted_concepts=json.dumps(concepts)
    )
    db.add(idea)
    db.commit()
    idea_id = idea.id
    db.close()

    console.print(f"\n[green]✓ Idea saved! (ID: {idea_id})[/green]")
    console.print("\n[cyan]Starting immediate check across all sources...[/cyan]")

    # Run immediate scan
    runner = DailyRunner()
    db = SessionLocal()
    idea_obj = db.query(Idea).filter_by(id=idea_id).first()
    results = runner._scan_for_idea(idea_obj, db)
    db.close()

    if results:
        console.print(f"\n[yellow]⚠️  Found {len(results)} similar products:[/yellow]\n")
        for comp in results:
            console.print(f"  • {comp['name']} ({comp['similarity_score']}% similar)")
            console.print(f"    Source: {comp['source']} | {comp['url']}")
            console.print(f"    [dim]{comp['reasoning']}[/dim]\n")
    else:
        console.print("\n[green]✓ No similar products found - your idea looks unique![/green]")

    console.print("\n[cyan]📧 Daily monitoring active - you'll get emails when new competitors appear[/cyan]")

def main():
    init_db()

    console.print("[bold]Idea Validator[/bold]")
    console.print("1. Add new idea")
    console.print("2. Start daily scheduler")

    choice = Prompt.ask("Choose", choices=["1", "2"])

    if choice == "1":
        onboarding()
    else:
        runner = DailyRunner()
        runner.start()

if __name__ == "__main__":
    main()
