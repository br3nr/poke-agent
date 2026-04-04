import asyncio
import argparse
import os
from dotenv import load_dotenv
import google.generativeai as genai
from rich import print

from poke_env import AccountConfiguration, ShowdownServerConfiguration
from poke_env.player import RandomPlayer

from classes.player import GeminiPlayer

load_dotenv()

BATTLE_FORMAT = "gen9randombattle"


def configure_gemini():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables")
    genai.configure(api_key=api_key)
    print("[bold green]Gemini API configured successfully[/bold green]")


async def test_locally(n_battles: int = 3):
    print(
        f"\n[bold cyan]Testing GeminiPlayer vs RandomPlayer ({n_battles} battles)[/bold cyan]\n"
    )

    gemini_player = GeminiPlayer(
        battle_format=BATTLE_FORMAT,
        max_concurrent_battles=1,
    )

    random_player = RandomPlayer(
        battle_format=BATTLE_FORMAT,
        max_concurrent_battles=1,
    )

    await gemini_player.battle_against(random_player, n_battles=n_battles)

    print(f"\n[bold cyan]{'=' * 60}[/bold cyan]")
    print(f"[bold cyan]Results[/bold cyan]")
    print(f"[bold cyan]{'=' * 60}[/bold cyan]")
    print(
        f"GeminiPlayer: {gemini_player.n_won_battles} wins / {gemini_player.n_finished_battles} battles"
    )
    print(f"Win rate: {gemini_player.win_rate * 100:.1f}%")
    print(f"[bold cyan]{'=' * 60}[/bold cyan]\n")


async def play_online():
    username = os.getenv("SHOWDOWN_USERNAME")
    password = os.getenv("SHOWDOWN_PASSWORD")

    if not username or not password:
        raise ValueError("SHOWDOWN_USERNAME and SHOWDOWN_PASSWORD required in .env")

    print(f"\n[bold cyan]Connecting to Pokemon Showdown as {username}[/bold cyan]\n")

    player = GeminiPlayer(
        account_configuration=AccountConfiguration(username, password),
        server_configuration=ShowdownServerConfiguration,
        battle_format=BATTLE_FORMAT,
        max_concurrent_battles=1,
    )

    print("[bold green]Waiting for challenges...[/bold green]")
    print("[dim]Challenge this bot on Pokemon Showdown to start a battle[/dim]")

    await player.accept_challenges(None, 10)


async def challenge_player(opponent: str):
    username = os.getenv("SHOWDOWN_USERNAME")
    password = os.getenv("SHOWDOWN_PASSWORD")

    if not username or not password:
        raise ValueError("SHOWDOWN_USERNAME and SHOWDOWN_PASSWORD required in .env")

    print(f"\n[bold cyan]Challenging {opponent} as {username}[/bold cyan]\n")

    player = GeminiPlayer(
        account_configuration=AccountConfiguration(username, password),
        server_configuration=ShowdownServerConfiguration,
        battle_format=BATTLE_FORMAT,
        max_concurrent_battles=1,
    )

    await player.send_challenges(opponent, n_challenges=1)


async def ladder(n_games: int = 5):
    username = os.getenv("SHOWDOWN_USERNAME")
    password = os.getenv("SHOWDOWN_PASSWORD")

    if not username or not password:
        raise ValueError("SHOWDOWN_USERNAME and SHOWDOWN_PASSWORD required in .env")

    print(f"\n[bold cyan]Playing {n_games} ladder games as {username}[/bold cyan]\n")

    player = GeminiPlayer(
        account_configuration=AccountConfiguration(username, password),
        server_configuration=ShowdownServerConfiguration,
        battle_format=BATTLE_FORMAT,
        max_concurrent_battles=1,
        start_timer_on_battle_start=True,
    )

    await player.ladder(n_games)

    print(f"\n[bold cyan]Ladder Results[/bold cyan]")
    print(f"Won: {player.n_won_battles} / {player.n_finished_battles}")
    print(f"Win rate: {player.win_rate * 100:.1f}%")


def main():
    parser = argparse.ArgumentParser(
        description="Poke-Agent: AI Pokemon Battle Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python showdown.py --test              # Test locally vs RandomPlayer
    python showdown.py --test -n 5         # Test 5 battles locally
    python showdown.py --online            # Accept challenges online
    python showdown.py --challenge br3nr   # Challenge a specific player
    python showdown.py --ladder            # Play on the ladder
        """,
    )

    parser.add_argument(
        "--test", action="store_true", help="Test against RandomPlayer locally"
    )
    parser.add_argument(
        "--online", action="store_true", help="Play online (accept challenges)"
    )
    parser.add_argument("--challenge", type=str, help="Challenge a specific player")
    parser.add_argument("--ladder", action="store_true", help="Play on the ladder")
    parser.add_argument(
        "-n",
        "--num-battles",
        type=int,
        default=3,
        help="Number of battles (for test/ladder)",
    )

    args = parser.parse_args()

    configure_gemini()

    if args.test:
        asyncio.run(test_locally(args.num_battles))
    elif args.online:
        asyncio.run(play_online())
    elif args.challenge:
        asyncio.run(challenge_player(args.challenge))
    elif args.ladder:
        asyncio.run(ladder(args.num_battles))
    else:
        print("[dim]No mode specified, running local test...[/dim]")
        print("[dim]Use --help to see available options[/dim]\n")
        asyncio.run(test_locally(args.num_battles))


if __name__ == "__main__":
    main()
