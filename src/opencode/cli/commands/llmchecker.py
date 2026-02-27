"""
CLI commands for LLM Checker functionality.

Provides commands for hardware detection, model recommendations,
Ollama management, and calibration.
"""

import asyncio
import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

app = typer.Typer(name="llm", help="LLM Checker commands")
console = Console()


@app.command("hw-detect")
def hardware_detect(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
    force: bool = typer.Option(False, "--force", "-f", help="Force refresh"),
):
    """Detect system hardware capabilities.
    
    Detects CPU, GPU, memory, and acceleration backends.
    """
    from ...llmchecker.hardware import HardwareDetector
    
    detector = HardwareDetector()
    info = detector.detect(force_refresh=force)
    
    if json_output:
        console.print_json(data=info.to_dict())
        return
    
    # Display summary
    console.print(Panel.fit(
        f"[bold cyan]{info.cpu.brand}[/bold cyan]\n"
        f"Tier: [bold]{info.tier.value.upper()}[/bold]\n"
        f"Max model size: [bold]{info.max_model_size_gb:.1f} GB[/bold]\n"
        f"Best backend: [bold]{info.backend.value}[/bold]",
        title="System Summary",
    ))
    
    # CPU info
    cpu_table = Table(title="CPU")
    cpu_table.add_column("Property", style="cyan")
    cpu_table.add_column("Value", style="green")
    cpu_table.add_row("Brand", info.cpu.brand)
    cpu_table.add_row("Cores", str(info.cpu.physical_cores))
    cpu_table.add_row("Threads", str(info.cpu.threads))
    cpu_table.add_row("Max Speed", f"{info.cpu.speed_max_ghz:.2f} GHz")
    cpu_table.add_row("Score", str(info.cpu.score))
    console.print(cpu_table)
    
    # Memory info
    mem_table = Table(title="Memory")
    mem_table.add_column("Property", style="cyan")
    mem_table.add_column("Value", style="green")
    mem_table.add_row("Total", f"{info.memory.total_gb} GB")
    mem_table.add_row("Available", f"{info.memory.available_gb} GB")
    mem_table.add_row("Used", f"{info.memory.used_gb} GB ({info.memory.usage_percent:.1f}%)")
    mem_table.add_row("Swap", f"{info.memory.swap_total_gb} GB")
    console.print(mem_table)
    
    # GPU info
    if info.gpus:
        gpu_table = Table(title="GPU(s)")
        gpu_table.add_column("Model", style="cyan")
        gpu_table.add_column("VRAM", style="green")
        gpu_table.add_column("Vendor", style="yellow")
        gpu_table.add_column("Score", style="magenta")
        
        for gpu in info.gpus:
            gpu_table.add_row(
                gpu.model,
                f"{gpu.vram_gb:.1f} GB",
                gpu.vendor.value,
                str(gpu.score),
            )
        console.print(gpu_table)
    else:
        console.print("[yellow]No GPU detected[/yellow]")


@app.command("recommend")
def recommend_models(
    category: str = typer.Option("general", "--category", "-c", help="Use case category"),
    limit: int = typer.Option(5, "--limit", "-l", help="Number of recommendations"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
    calibrated: Optional[Path] = typer.Option(None, "--calibrated", help="Use calibrated policy"),
):
    """Get model recommendations based on hardware.
    
    Categories: general, coding, reasoning, chat, vision
    """
    from ...llmchecker.hardware import HardwareDetector
    from ...llmchecker.scoring import ScoringEngine, ModelInfo, ScoringWeights
    from ...llmchecker.calibration import CalibrationManager
    
    # Get hardware info
    detector = HardwareDetector()
    system_info = detector.detect()
    
    # Check for calibrated policy
    policy = None
    if calibrated:
        manager = CalibrationManager()
        policy = manager.load_policy(calibrated)
    else:
        # Try to discover default policy
        manager = CalibrationManager()
        policy = manager.discover_policy()
    
    if policy:
        recommended_model = policy.get_model_for_task(category)
        console.print(f"[green]Calibrated recommendation:[/green] {recommended_model}")
    
    # Get installed models from Ollama
    try:
        from ...llmchecker.ollama import OllamaClient
        
        async def get_models():
            client = OllamaClient()
            return await client.list_models()
        
        models = asyncio.run(get_models())
    except Exception as e:
        console.print(f"[yellow]Could not fetch Ollama models: {e}[/yellow]")
        models = []
    
    if not models:
        console.print("[yellow]No models found. Install some with 'ollama pull <model>'[/yellow]")
        return
    
    # Create model info objects
    model_infos = []
    for m in models:
        info = ModelInfo(
            name=m.name,
            family=m.family or m.name.split(":")[0],
            parameters_b=m.parameters_b,
            size_gb=m.size_gb,
        )
        model_infos.append(info)
    
    # Score models
    engine = ScoringEngine(system_info)
    weights = ScoringWeights.for_use_case(category)
    result = engine.score_models(model_infos, category, weights)
    
    if json_output:
        output = {
            "hardware": system_info.to_dict(),
            "recommendations": [s.to_dict() for s in result.get_top_n(limit)],
        }
        console.print_json(data=output)
        return
    
    # Display recommendations
    table = Table(title=f"Top {limit} Models for {category}")
    table.add_column("Rank", style="cyan", width=5)
    table.add_column("Model", style="green")
    table.add_column("Quality", style="yellow")
    table.add_column("Speed", style="magenta")
    table.add_column("Fit", style="blue")
    table.add_column("Final", style="bold")
    
    for score in result.get_top_n(limit):
        table.add_row(
            str(score.rank),
            score.model.name,
            f"{score.quality_score:.0f}",
            f"{score.speed_score:.0f}",
            f"{score.fit_score:.0f}",
            f"{score.final_score:.0f}",
        )
    
    console.print(table)


@app.command("ollama-list")
def ollama_list(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
):
    """List installed Ollama models."""
    from ...llmchecker.ollama import OllamaClient
    
    async def list_models():
        client = OllamaClient()
        availability = await client.check_availability()
        
        if not availability.get("available"):
            console.print(f"[red]Ollama not available: {availability.get('error')}[/red]")
            return None
        
        return await client.list_models()
    
    models = asyncio.run(list_models())
    
    if models is None:
        return
    
    if json_output:
        console.print_json(data=[m.to_dict() for m in models])
        return
    
    if not models:
        console.print("[yellow]No models installed[/yellow]")
        return
    
    table = Table(title="Installed Models")
    table.add_column("Name", style="cyan")
    table.add_column("Size", style="green")
    table.add_column("Family", style="yellow")
    table.add_column("Parameters", style="magenta")
    table.add_column("Quantization", style="blue")
    
    for model in models:
        table.add_row(
            model.name,
            f"{model.size_gb:.1f} GB",
            model.family or "-",
            model.parameter_size or "-",
            model.quantization_level or "-",
        )
    
    console.print(table)


@app.command("ollama-pull")
def ollama_pull(
    model: str = typer.Argument(..., help="Model name to pull (e.g., llama3.2:3b or hf.co/user/repo)"),
):
    """Pull a model from Ollama registry or Hugging Face.
    
    Supports:
    - Ollama registry: llama3.2:3b
    - Hugging Face: hf.co/{username}/{repository}
    - Hugging Face with quantization: hf.co/{username}/{repository}:{quantization}
    """
    from ...llmchecker.ollama import OllamaClient
    
    async def pull():
        client = OllamaClient()
        
        # Check if it's a Hugging Face model
        if client.is_huggingface_model(model):
            hf_info = client.parse_huggingface_model(model)
            display_name = f"{hf_info.get('full_name', model)}"
            if hf_info.get('quantization'):
                display_name += f" (quantization: {hf_info['quantization']})"
            console.print(f"[cyan]Pulling from Hugging Face: {display_name}[/cyan]")
        else:
            display_name = model
        
        with console.status(f"[bold green]Pulling {display_name}...") as status:
            async for progress in client.pull_model(model):
                if progress.status == "success":
                    console.print(f"[green]Successfully pulled {display_name}[/green]")
                elif progress.total > 0:
                    percent = progress.percent
                    status.update(f"[bold green]Pulling {display_name}... {percent:.1f}%")
                else:
                    status.update(f"[bold green]{progress.status}...")
    
    asyncio.run(pull())


@app.command("ollama-run")
def ollama_run(
    model: str = typer.Argument(..., help="Model name (e.g., llama3.2:3b or hf.co/user/repo)"),
    prompt: str = typer.Argument(..., help="Prompt to run"),
):
    """Run a prompt against a model.
    
    Supports:
    - Ollama models: llama3.2:3b
    - Hugging Face models: hf.co/{username}/{repository}
    
    If the model is not installed, it will be pulled automatically.
    """
    from ...llmchecker.ollama import OllamaClient
    
    async def run():
        client = OllamaClient()
        
        # Normalize model name
        normalized_model = client._normalize_model_name(model)
        
        # Check if it's a Hugging Face model
        if client.is_huggingface_model(model):
            hf_info = client.parse_huggingface_model(model)
            display_name = f"hf.co/{hf_info.get('full_name', model)}"
            console.print(f"[cyan]Using Hugging Face model: {display_name}[/cyan]")
        else:
            display_name = normalized_model
        
        with console.status(f"[bold green]Running {display_name}..."):
            response = await client.generate(normalized_model, prompt)
        
        console.print(Panel(response.content, title=f"Response from {display_name}"))
        console.print(f"[dim]Tokens/sec: {response.tokens_per_second:.2f}[/dim]")
        console.print(f"[dim]Time: {response.total_time_seconds:.2f}s[/dim]")
    
    asyncio.run(run())


@app.command("calibrate")
def calibrate(
    suite: Path = typer.Option(..., "--suite", "-s", help="Prompt suite file (JSONL)"),
    models: list[str] = typer.Option(..., "--model", "-m", help="Models to calibrate"),
    objective: str = typer.Option("balanced", "--objective", "-o", help="Calibration objective"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate without running"),
    output: Optional[Path] = typer.Option(None, "--output", help="Output file for results"),
    policy_out: Optional[Path] = typer.Option(None, "--policy-out", help="Output file for policy"),
):
    """Run calibration on models.
    
    Objectives: speed, quality, balanced, cost
    """
    from ...llmchecker.calibration import CalibrationManager, CalibrationObjective
    
    manager = CalibrationManager()
    
    # Parse prompt suite
    try:
        prompts = manager.parse_prompt_suite(suite)
        console.print(f"[green]Loaded {len(prompts)} prompts from suite[/green]")
    except Exception as e:
        console.print(f"[red]Failed to load prompt suite: {e}[/red]")
        raise typer.Exit(1)
    
    # Map objective
    obj_map = {
        "speed": CalibrationObjective.SPEED,
        "quality": CalibrationObjective.QUALITY,
        "balanced": CalibrationObjective.BALANCED,
        "cost": CalibrationObjective.COST,
    }
    obj = obj_map.get(objective.lower(), CalibrationObjective.BALANCED)
    
    # Progress callback
    def progress(model: str, completed: int, total: int):
        percent = (completed / total) * 100 if total > 0 else 0
        console.print(f"[dim]{model}: {completed}/{total} ({percent:.0f}%)[/dim]")
    
    # Run calibration
    async def run_calibration():
        with console.status("[bold green]Running calibration..."):
            return await manager.run_calibration(
                models=models,
                prompt_suite=prompts,
                objective=obj,
                dry_run=dry_run,
                progress_callback=progress,
            )
    
    result = asyncio.run(run_calibration())
    
    # Display results
    console.print(f"\n[bold]Calibration Complete[/bold]")
    console.print(f"Best model: [green]{result.best_model}[/green]")
    console.print(f"Duration: {result.duration_seconds:.1f}s")
    
    # Model results table
    table = Table(title="Model Results")
    table.add_column("Model", style="cyan")
    table.add_column("Avg Speed", style="green")
    table.add_column("Avg Quality", style="yellow")
    table.add_column("Success Rate", style="magenta")
    table.add_column("Score", style="bold")
    
    for mr in sorted(result.model_results, key=lambda x: x.overall_score, reverse=True):
        table.add_row(
            mr.model,
            f"{mr.avg_tokens_per_second:.1f} tok/s",
            f"{mr.avg_quality_score:.0f}",
            f"{mr.success_rate * 100:.0f}%",
            f"{mr.overall_score:.0f}",
        )
    
    console.print(table)
    
    # Save results
    if output:
        manager.save_result(result, output)
        console.print(f"[green]Results saved to {output}[/green]")
    
    # Generate and save policy
    if policy_out:
        policy = manager.generate_policy(result)
        manager.save_policy(policy, policy_out)
        console.print(f"[green]Policy saved to {policy_out}[/green]")


@app.command("policy")
def policy_command(
    action: str = typer.Argument(..., help="Action: init, validate, show"),
    path: Optional[Path] = typer.Argument(None, help="Policy file path"),
):
    """Manage calibration policies.
    
    Actions:
    - init: Create a new policy template
    - validate: Validate a policy file
    - show: Show current policy
    """
    from ...llmchecker.calibration import CalibrationManager, CalibrationPolicy
    
    manager = CalibrationManager()
    
    if action == "init":
        if not path:
            path = Path("calibration-policy.yaml")
        
        # Create template policy
        policy = CalibrationPolicy(
            name="my-policy",
            description="Custom calibration policy",
            default_model="llama3.2:3b",
            rules=[],
        )
        
        manager.save_policy(policy, path)
        console.print(f"[green]Created policy template at {path}[/green]")
    
    elif action == "validate":
        if not path:
            console.print("[red]Please specify a policy file[/red]")
            raise typer.Exit(1)
        
        try:
            policy = manager.load_policy(path)
            console.print(f"[green]Policy is valid: {policy.name}[/green]")
            console.print(f"  Default model: {policy.default_model}")
            console.print(f"  Rules: {len(policy.rules)}")
        except Exception as e:
            console.print(f"[red]Invalid policy: {e}[/red]")
            raise typer.Exit(1)
    
    elif action == "show":
        policy = manager.discover_policy()
        
        if not policy:
            console.print("[yellow]No policy found[/yellow]")
            return
        
        console.print(f"[bold]Policy: {policy.name}[/bold]")
        console.print(f"Default model: {policy.default_model}")
        console.print(f"Calibration ID: {policy.calibration_id}")
        
        if policy.rules:
            table = Table(title="Routing Rules")
            table.add_column("Task", style="cyan")
            table.add_column("Model", style="green")
            table.add_column("Priority", style="yellow")
            
            for rule in policy.rules:
                table.add_row(rule.task, rule.model, str(rule.priority))
            
            console.print(table)
    
    else:
        console.print(f"[red]Unknown action: {action}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
