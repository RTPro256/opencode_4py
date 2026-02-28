"""
Skills CLI Commands for SkillPointer Integration.

Provides command-line interface for managing skills with the SkillPointer architecture.

Commands:
- setup: Migrate skills to pointer architecture
- migrate: Migrate existing skills to vault
- generate: Generate category pointers
- list: List categories and skills
- stats: Show token savings statistics
- revert: Revert from pointer architecture
"""

import typer
from rich.console import Console
from rich.table import Table

from opencode.skills.pointer import (
    SkillPointerManager,
    categorize_skill,
    get_categories,
    estimate_token_savings,
    is_pointer_skill,
    extract_category,
)

app = typer.Typer(name="skills", help="Skills management commands")
console = Console()


@app.command("setup")
def setup_skillpointer(
    vault_dir: str = typer.Option(
        None,
        "--vault",
        "-v",
        help="Custom vault directory path",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be done without making changes",
    ),
):
    """
    Set up SkillPointer architecture.
    
    This command will:
    1. Migrate all skills to the hidden vault
    2. Generate category pointers
    3. Save pointers to active skills directory
    """
    from pathlib import Path
    
    console.print("\n[bold cyan]SkillPointer Setup[/bold cyan]\n")
    
    # Initialize manager
    manager = SkillPointerManager(
        vault_dir=Path(vault_dir) if vault_dir else None,
    )
    
    # Show current state
    console.print(f"Active skills directory: [blue]{manager.active_skills_dir}[/blue]")
    console.print(f"Vault directory: [blue]{manager.vault_dir}[/blue]")
    
    # Count current skills
    if manager.active_skills_dir.exists():
        skill_count = sum(
            1 for f in manager.active_skills_dir.iterdir()
            if f.is_dir() and not f.name.endswith("-category-pointer")
        )
        console.print(f"Current skills found: [yellow]{skill_count}[/yellow]")
        
        # Estimate savings
        savings = estimate_token_savings(skill_count)
        console.print(f"\n[bold]Token Savings Estimate:[/bold]")
        console.print(f"  Traditional startup: ~{savings['traditional_tokens']:,} tokens")
        console.print(f"  With pointers: ~{savings['pointer_tokens']:,} tokens")
        console.print(f"  Savings: [green]{savings['savings_percent']:.1f}%[/green]")
    else:
        console.print("[yellow]No active skills directory found.[/yellow]")
        return
    
    if dry_run:
        console.print("\n[yellow]Dry run mode - no changes made.[/yellow]")
        return
    
    # Confirm
    console.print("\n[yellow]This will move skills to the vault and create category pointers.[/yellow]")
    confirm = typer.confirm("Continue?")
    
    if not confirm:
        console.print("[yellow]Setup cancelled.[/yellow]")
        return
    
    # Run setup
    result = manager.setup()
    
    console.print(f"\n[bold green]Setup Complete![/bold green]\n")
    console.print(f"  Skills migrated: [cyan]{result['skills_migrated']}[/cyan]")
    console.print(f"  Categories: [cyan]{result['categories']}[/cyan]")
    console.print(f"  Pointers created: [cyan]{result['pointers_created']}[/cyan]")
    console.print(f"  Vault location: [blue]{result['vault_path']}[/blue]")


@app.command("migrate")
def migrate_skills(
    category: str = typer.Option(
        None,
        "--category",
        "-c",
        help="Specific category to migrate (default: all)",
    ),
    vault_dir: str = typer.Option(
        None,
        "--vault",
        "-v",
        help="Custom vault directory path",
    ),
):
    """
    Migrate skills to the hidden vault.
    
    Skills are moved from the active skills directory to the vault,
    organized by category.
    """
    from pathlib import Path
    
    console.print("\n[bold cyan]Migrating Skills to Vault[/bold cyan]\n")
    
    manager = SkillPointerManager(
        vault_dir=Path(vault_dir) if vault_dir else None,
    )
    
    if not manager.active_skills_dir.exists():
        console.print(f"[red]Active skills directory not found: {manager.active_skills_dir}[/red]")
        return
    
    category_counts = manager.migrate_skills()
    
    console.print(f"\n[bold green]Migration Complete![/bold green]\n")
    
    table = Table(title="Skills by Category")
    table.add_column("Category", style="cyan")
    table.add_column("Skills", style="green", justify="right")
    
    for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        table.add_row(cat, str(count))
    
    console.print(table)
    
    total = sum(category_counts.values())
    console.print(f"\n[bold]Total: {total} skills migrated[/bold]")


@app.command("generate")
def generate_pointers(
    vault_dir: str = typer.Option(
        None,
        "--vault",
        "-v",
        help="Custom vault directory path",
    ),
    save: bool = typer.Option(
        True,
        "--save/--no-save",
        help="Save pointers to active skills directory",
    ),
):
    """
    Generate category pointers from vault.
    
    Scans the vault and creates lightweight category pointer skills
    that index all skills in each category.
    """
    from pathlib import Path
    
    console.print("\n[bold cyan]Generating Category Pointers[/bold cyan]\n")
    
    manager = SkillPointerManager(
        vault_dir=Path(vault_dir) if vault_dir else None,
    )
    
    pointers = manager.generate_pointers()
    
    console.print(f"\n[bold]Generated {len(pointers)} category pointers:[/bold]\n")
    
    table = Table()
    table.add_column("Category", style="cyan")
    table.add_column("Skills", style="green", justify="right")
    table.add_column("Trigger", style="yellow")
    
    for cat, pointer in sorted(pointers.items()):
        table.add_row(
            cat,
            str(pointer.skill_count),
            pointer.trigger,
        )
    
    console.print(table)
    
    if save:
        saved = manager.save_pointers()
        console.print(f"\n[bold green]Saved {saved} pointers to active skills directory[/bold green]")


@app.command("list")
def list_categories(
    vault_dir: str = typer.Option(
        None,
        "--vault",
        "-v",
        help="Custom vault directory path",
    ),
    show_skills: bool = typer.Option(
        False,
        "--skills",
        "-s",
        help="Show individual skills in each category",
    ),
):
    """
    List available skill categories.
    """
    from pathlib import Path
    
    manager = SkillPointerManager(
        vault_dir=Path(vault_dir) if vault_dir else None,
    )
    
    if not manager.vault_dir.exists():
        console.print(f"[yellow]No vault found at {manager.vault_dir}[/yellow]")
        console.print("Run 'skills setup' to initialize SkillPointer.")
        return
    
    pointers = manager.generate_pointers()
    
    console.print(f"\n[bold]Available Categories ({len(pointers)}):[/bold]\n")
    
    table = Table()
    table.add_column("Category", style="cyan")
    table.add_column("Skills", style="green", justify="right")
    
    for cat, pointer in sorted(pointers.items()):
        table.add_row(cat, str(pointer.skill_count))
    
    console.print(table)
    
    if show_skills:
        console.print("\n[bold]Skills in Vault:[/bold]\n")
        for cat, pointer in sorted(pointers.items()):
            skills = manager.get_vault_skills(cat)
            console.print(f"\n[cyan]{cat}:[/cyan]")
            for skill_file in skills[:10]:
                console.print(f"  - {skill_file.stem}")
            if len(skills) > 10:
                console.print(f"  ... and {len(skills) - 10} more")


@app.command("stats")
def show_stats(
    vault_dir: str = typer.Option(
        None,
        "--vault",
        "-v",
        help="Custom vault directory path",
    ),
):
    """
    Show token savings statistics.
    """
    from pathlib import Path
    
    manager = SkillPointerManager(
        vault_dir=Path(vault_dir) if vault_dir else None,
    )
    
    # Count skills
    skill_count = 0
    if manager.active_skills_dir.exists():
        skill_count = sum(
            1 for f in manager.active_skills_dir.iterdir()
            if f.is_dir() and not f.name.endswith("-category-pointer")
        )
    
    if manager.vault_dir.exists():
        for cat_dir in manager.vault_dir.iterdir():
            if cat_dir.is_dir():
                skill_count += sum(1 for _ in cat_dir.rglob("SKILL.md"))
    
    if skill_count == 0:
        console.print("[yellow]No skills found.[/yellow]")
        console.print("Run 'skills setup' to initialize SkillPointer.")
        return
    
    savings = estimate_token_savings(skill_count)
    
    console.print(f"\n[bold]Skill Library Statistics[/bold]\n")
    console.print(f"Total skills: [cyan]{skill_count}[/cyan]\n")
    console.print(f"[bold]Token Analysis:[/bold]")
    console.print(f"  Traditional startup:     ~{savings['traditional_tokens']:>8,} tokens")
    console.print(f"  With SkillPointer:       ~{savings['pointer_tokens']:>8,} tokens")
    console.print(f"  [bold]Savings:[/bold]             [green]{savings['savings_tokens']:>8,} tokens ({savings['savings_percent']:.1f}%)[/green]")


@app.command("categorize")
def categorize(
    skill_name: str = typer.Argument(..., help="Name of the skill to categorize"),
):
    """
    Show which category a skill would belong to.
    """
    category = categorize_skill(skill_name)
    console.print(f"\n[bold]{skill_name}[/bold] -> [cyan]{category}[/cyan]")


@app.command("categories")
def list_all_categories():
    """
    List all available category names.
    """
    categories = get_categories()
    
    console.print(f"\n[bold]Available Categories ({len(categories)}):[/bold]\n")
    
    # Display in columns
    cols = 4
    for i in range(0, len(categories), cols):
        row = categories[i:i+cols]
        console.print("  ".join(f"[cyan]{c}[/cyan]" for c in row))


@app.command("revert")
def revert_pointers(
    vault_dir: str = typer.Option(
        None,
        "--vault",
        "-v",
        help="Custom vault directory path",
    ),
    keep_vault: bool = typer.Option(
        True,
        "--keep-vault/--delete-vault",
        help="Keep or delete the vault after reverting",
    ),
):
    """
    Revert from SkillPointer architecture.
    
    Moves skills back from vault to active directory.
    """
    from pathlib import Path
    import shutil
    
    console.print("\n[bold cyan]Reverting from SkillPointer[/bold cyan]\n")
    
    manager = SkillPointerManager(
        vault_dir=Path(vault_dir) if vault_dir else None,
    )
    
    if not manager.vault_dir.exists():
        console.print("[yellow]No vault found.[/yellow]")
        return
    
    confirm = typer.confirm(
        f"This will move skills from {manager.vault_dir} back to {manager.active_skills_dir}. Continue?"
    )
    
    if not confirm:
        console.print("[yellow]Revert cancelled.[/yellow]")
        return
    
    # Move skills back
    moved = 0
    for cat_dir in list(manager.vault_dir.iterdir()):
        if not cat_dir.is_dir():
            continue
        
        for skill_dir in list(cat_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            
            dest = manager.active_skills_dir / skill_dir.name
            if dest.exists():
                shutil.rmtree(dest)
            
            shutil.move(str(skill_dir), str(dest))
            moved += 1
    
    # Delete pointers
    for f in manager.active_skills_dir.iterdir():
        if f.is_dir() and f.name.endswith("-category-pointer"):
            shutil.rmtree(f)
    
    # Optionally delete vault
    if not keep_vault and manager.vault_dir.exists():
        shutil.rmtree(manager.vault_dir)
    
    console.print(f"\n[bold green]Reverted {moved} skills back to active directory[/bold green]")
    
    if not keep_vault:
        console.print(f"[yellow]Deleted vault directory[/yellow]")


if __name__ == "__main__":
    app()
