from typing import Any, Optional
import io
import os
import re

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

# log levels
MINIMAL = 0
VERBOSE = 1

_log_level = MINIMAL
_file_console: Optional[Console] = None
_log_file: Optional[io.TextIOWrapper] = None

# per-battle log
_battle_file: Optional[io.TextIOWrapper] = None
_battle_file_console: Optional[Console] = None
_battle_count = 0
_log_dir = "logs"

# ── token tracking ───────────────────────────────────────────

_total_prompt_tokens = 0
_total_completion_tokens = 0
_total_thinking_tokens = 0
_total_requests = 0


def set_log_level(level: int):
    global _log_level
    _log_level = level


def get_log_level() -> int:
    return _log_level


def is_verbose() -> bool:
    return _log_level >= VERBOSE


def set_log_file(path: str):
    """Open a file for verbose logging. The file always receives verbose output."""
    global _file_console, _log_file
    _log_file = open(path, "w")
    _file_console = Console(file=_log_file, no_color=True, width=120)


def close_log_file():
    """Flush and close the log file if open."""
    global _file_console, _log_file
    _close_battle_log()
    if _log_file:
        _log_file.close()
        _log_file = None
        _file_console = None


def _sanitize_filename(name: str) -> str:
    """Remove characters that aren't safe for filenames."""
    return re.sub(r"[^\w\-]", "_", name)


def _open_battle_log(opponent: str):
    """Open a per-battle log file in the logs/ directory."""
    global _battle_file, _battle_file_console, _battle_count
    _close_battle_log()

    _battle_count += 1
    os.makedirs(_log_dir, exist_ok=True)
    safe_opponent = _sanitize_filename(opponent)
    filename = f"battle_{_battle_count:03d}_vs_{safe_opponent}.log"
    filepath = os.path.join(_log_dir, filename)

    _battle_file = open(filepath, "w")
    _battle_file_console = Console(file=_battle_file, no_color=True, width=120)


def _close_battle_log():
    """Close the current per-battle log file if open."""
    global _battle_file, _battle_file_console
    if _battle_file:
        _battle_file.close()
        _battle_file = None
        _battle_file_console = None


def _fprint(*args, **kwargs):
    """Print to all active file consoles (combined log + per-battle log)."""
    if _file_console:
        _file_console.print(*args, **kwargs)
    if _battle_file_console:
        _battle_file_console.print(*args, **kwargs)


# ── turn header ──────────────────────────────────────────────


def log_turn_header(turn: int, your_pokemon: str, opponent_pokemon: str):
    """Always shown. The main turn separator."""
    your = Text(your_pokemon, style="bold green")
    vs = Text(" vs ", style="dim")
    opp = Text(opponent_pokemon, style="bold red")
    title = Text.assemble("Turn ", str(turn), style="bold cyan")

    matchup = Text.assemble(your, vs, opp)
    panel = Panel(
        matchup,
        title=title,
        border_style="cyan",
        padding=(0, 2),
    )
    console.print()
    console.print(panel)

    _fprint()
    _fprint(f"{'=' * 50}")
    _fprint(f"Turn {turn}: {your_pokemon} vs {opponent_pokemon}")
    _fprint(f"{'=' * 50}")


# ── phase markers ────────────────────────────────────────────


def log_phase(phase_num: int, name: str):
    """Verbose only. Shows which agent phase is running."""
    if is_verbose():
        console.print(
            f"  [dim]Phase {phase_num}:[/dim] [bold bright_blue]{name}[/bold bright_blue]"
        )
    _fprint(f"\nPhase {phase_num}: {name}")


# ── analysis ─────────────────────────────────────────────────


def log_analysis(analysis: str):
    """Verbose only. Full analysis dump."""
    if is_verbose():
        console.print()
        console.print(
            Panel(
                analysis,
                title="[bold bright_yellow]Analysis[/bold bright_yellow]",
                border_style="bright_yellow",
                padding=(1, 2),
            )
        )
    _fprint(f"\n--- Analysis ---")
    _fprint(analysis)
    _fprint(f"--- End Analysis ---")


# ── decision reasoning ───────────────────────────────────────


def log_decision_reasoning(reasoning: str):
    """Verbose only. Full LLM decision output."""
    if is_verbose():
        console.print()
        console.print(
            Panel(
                reasoning,
                title="[bold magenta]Decision Reasoning[/bold magenta]",
                border_style="magenta",
                padding=(1, 2),
            )
        )
    _fprint(f"\n--- Decision Reasoning ---")
    _fprint(reasoning)
    _fprint(f"--- End Decision Reasoning ---")


# ── final order ──────────────────────────────────────────────


def log_order(order_message: str):
    """Always shown. The action being taken."""
    action = order_message.lstrip("/")
    console.print(f"  [bold bright_green]>>> {action}[/bold bright_green]")
    _fprint(f">>> {action}")


# ── warnings / fallbacks ─────────────────────────────────────


def log_warning(message: str):
    """Always shown."""
    console.print(f"  [bold yellow]! {message}[/bold yellow]")
    _fprint(f"! {message}")


def log_error(message: str):
    """Always shown."""
    console.print(f"  [bold red]✗ {message}[/bold red]")
    _fprint(f"ERROR: {message}")


def log_info(message: str):
    """Always shown. General info line."""
    console.print(f"  [dim]{message}[/dim]")
    _fprint(message)


# ── agent function calls (debug) ─────────────────────────────


def log_agent_call(fn_name: str, fn_input: str, fn_output: Any = None):
    """Verbose only. Shows individual state-builder lookups."""
    if is_verbose():
        header = f"[dim cyan]{fn_name}[/dim cyan]([dim]{fn_input}[/dim])"
        console.print(f"    {header}")
    _fprint(f"    {fn_name}({fn_input})")


# ── battle agent action ──────────────────────────────────────


def log_battle_action(action_type: str, name: str, is_fallback: bool = False):
    """Verbose only. Shows what the battle agent parsed."""
    if is_verbose():
        if is_fallback:
            console.print(f"    [yellow]Fallback {action_type}: {name}[/yellow]")
        else:
            console.print(
                f"    [bright_red]Battle Agent: {action_type} {name}[/bright_red]"
            )
    prefix = "Fallback" if is_fallback else "Battle Agent:"
    _fprint(f"    {prefix} {action_type} {name}")


# ── rate limit ────────────────────────────────────────────────


def log_rate_limit():
    """Always shown."""
    console.print("  [dim magenta]Rate limited, waiting...[/dim magenta]")
    _fprint("Rate limited, waiting...")


# ── startup / results ─────────────────────────────────────────


def log_startup(message: str):
    """Always shown. Top-level startup info."""
    console.print(f"[bold cyan]{message}[/bold cyan]")
    _fprint(message)


def log_battle_start(
    opponent: str, your_rating: Optional[int], opponent_rating: Optional[int]
):
    """Always shown. Logs opponent name and both ELO ratings at battle start."""
    _open_battle_log(opponent)

    your_elo = str(your_rating) if your_rating is not None else "?"
    opp_elo = str(opponent_rating) if opponent_rating is not None else "?"

    body = f"vs [bold red]{opponent}[/bold red]  ·  You: [bold]{your_elo}[/bold]  ·  Opponent: [bold]{opp_elo}[/bold]"
    panel = Panel(
        body,
        title="[bold bright_green]Battle Start[/bold bright_green]",
        border_style="bright_green",
        padding=(0, 2),
    )
    console.print()
    console.print(panel)

    _fprint()
    _fprint(f"Battle Start: vs {opponent}  ·  You: {your_elo}  ·  Opponent: {opp_elo}")


def log_battle_end(
    won: bool,
    opponent: str,
    your_rating: Optional[int],
    opponent_rating: Optional[int],
    rating_change: Optional[int],
):
    """Always shown. Logs post-battle ELO and change."""
    result_str = "[bold green]WIN[/bold green]" if won else "[bold red]LOSS[/bold red]"
    your_elo = str(your_rating) if your_rating is not None else "?"
    opp_elo = str(opponent_rating) if opponent_rating is not None else "?"

    parts = [
        f"Result: {result_str} vs [bold]{opponent}[/bold]",
        f"Your ELO: [bold]{your_elo}[/bold]  ·  Opponent ELO: [bold]{opp_elo}[/bold]",
    ]
    if rating_change is not None:
        sign = "+" if rating_change >= 0 else ""
        change_style = "green" if rating_change >= 0 else "red"
        parts.append(
            f"ELO Change: [{change_style}]{sign}{rating_change}[/{change_style}]"
        )

    body = "\n".join(parts)
    panel = Panel(
        body,
        title="[bold bright_yellow]Battle End[/bold bright_yellow]",
        border_style="bright_yellow",
        padding=(0, 2),
    )
    console.print()
    console.print(panel)

    # file log (plain text)
    result_plain = "WIN" if won else "LOSS"
    _fprint()
    _fprint(f"Battle End: {result_plain} vs {opponent}")
    _fprint(f"  Your ELO: {your_elo}  ·  Opponent ELO: {opp_elo}")
    if rating_change is not None:
        sign = "+" if rating_change >= 0 else ""
        _fprint(f"  ELO Change: {sign}{rating_change}")

    _close_battle_log()


def log_results(won: int, total: int, win_rate: float):
    """Always shown. End-of-session results."""
    console.print()
    panel = Panel(
        f"[bold]{won}[/bold] / [bold]{total}[/bold] wins  ·  [bold]{win_rate:.1f}%[/bold] win rate",
        title="[bold cyan]Results[/bold cyan]",
        border_style="cyan",
        padding=(0, 2),
    )
    console.print(panel)

    _fprint()
    _fprint(f"Results: {won} / {total} wins  ·  {win_rate:.1f}% win rate")


# ── token usage ───────────────────────────────────────────────


def log_token_usage(
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    thinking_tokens: Optional[int] = None,
):
    """Track token usage per LLM call. Verbose: prints per-call. Always: accumulates."""
    global \
        _total_prompt_tokens, \
        _total_completion_tokens, \
        _total_thinking_tokens, \
        _total_requests
    _total_prompt_tokens += prompt_tokens or 0
    _total_completion_tokens += completion_tokens or 0
    _total_thinking_tokens += thinking_tokens or 0
    _total_requests += 1

    if is_verbose():
        parts = [f"in={prompt_tokens}", f"out={completion_tokens}"]
        if thinking_tokens:
            parts.append(f"think={thinking_tokens}")
        console.print(f"    [dim]tokens: {', '.join(parts)}[/dim]")

    parts_f = [f"in={prompt_tokens}", f"out={completion_tokens}"]
    if thinking_tokens:
        parts_f.append(f"think={thinking_tokens}")
    _fprint(f"    tokens: {', '.join(parts_f)}")


def log_token_summary():
    """Always shown at end of session. Prints cumulative token usage."""
    if _total_requests == 0:
        return

    lines = [
        f"LLM calls: {_total_requests}",
        f"Prompt tokens: {_total_prompt_tokens:,}",
        f"Completion tokens: {_total_completion_tokens:,}",
    ]
    if _total_thinking_tokens > 0:
        lines.append(f"Thinking tokens: {_total_thinking_tokens:,}")
    lines.append(
        f"Total tokens: {_total_prompt_tokens + _total_completion_tokens + _total_thinking_tokens:,}"
    )

    body = "\n".join(lines)
    console.print(
        Panel(
            body,
            title="[bold bright_blue]Token Usage[/bold bright_blue]",
            border_style="bright_blue",
            padding=(0, 2),
        )
    )

    _fprint()
    _fprint("Token Usage:")
    for line in lines:
        _fprint(f"  {line}")


def reset_token_usage():
    """Reset counters (e.g. between battles)."""
    global \
        _total_prompt_tokens, \
        _total_completion_tokens, \
        _total_thinking_tokens, \
        _total_requests
    _total_prompt_tokens = 0
    _total_completion_tokens = 0
    _total_thinking_tokens = 0
    _total_requests = 0


# ── keep backward compat for old callers ──────────────────────


def print_agent_function_call(fn_name: str, fn_input: str, fn_output: Any = "N/A"):
    log_agent_call(fn_name, fn_input, fn_output)
