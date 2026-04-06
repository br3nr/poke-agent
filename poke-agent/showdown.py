import asyncio
import argparse
import os
from dotenv import load_dotenv

from poke_env import AccountConfiguration, ShowdownServerConfiguration
from poke_env.player import RandomPlayer
from poke_env.concurrency import POKE_LOOP

from classes.player import GeminiPlayer
from utils.logging import (
    log_startup,
    log_info,
    log_results,
    log_warning,
    log_token_summary,
    set_log_level,
    set_log_file,
    close_log_file,
    MINIMAL,
    VERBOSE,
)

load_dotenv()

BATTLE_FORMAT = "gen9randombattle"


async def forfeit_on_cancel(player: GeminiPlayer, coro):
    try:
        return await coro
    except asyncio.CancelledError:
        log_warning("Interrupted — forfeiting active battles...")
        future = asyncio.run_coroutine_threadsafe(
            player.forfeit_active_battles(), POKE_LOOP
        )
        try:
            future.result(timeout=5)
        except Exception:
            pass
        log_info("Resigned and exiting.")


def check_api_key():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables")
    log_info("Gemini API key found")


async def test_locally(n_battles: int = 3):
    log_startup(f"Testing GeminiPlayer vs RandomPlayer ({n_battles} battles)")

    gemini_player = GeminiPlayer(
        battle_format=BATTLE_FORMAT,
        max_concurrent_battles=1,
    )

    random_player = RandomPlayer(
        battle_format=BATTLE_FORMAT,
        max_concurrent_battles=1,
    )

    await forfeit_on_cancel(
        gemini_player,
        gemini_player.battle_against(random_player, n_battles=n_battles),
    )

    log_results(
        gemini_player.n_won_battles,
        gemini_player.n_finished_battles,
        gemini_player.win_rate * 100 if gemini_player.n_finished_battles > 0 else 0,
    )


async def play_online():
    username = os.getenv("SHOWDOWN_USERNAME")
    password = os.getenv("SHOWDOWN_PASSWORD")

    if not username or not password:
        raise ValueError("SHOWDOWN_USERNAME and SHOWDOWN_PASSWORD required in .env")

    log_startup(f"Connecting to Pokemon Showdown as {username}")

    player = GeminiPlayer(
        account_configuration=AccountConfiguration(username, password),
        server_configuration=ShowdownServerConfiguration,
        battle_format=BATTLE_FORMAT,
        max_concurrent_battles=1,
    )

    log_info("Waiting for challenges...")
    await forfeit_on_cancel(player, player.accept_challenges(None, 10))


async def challenge_player(opponent: str):
    username = os.getenv("SHOWDOWN_USERNAME")
    password = os.getenv("SHOWDOWN_PASSWORD")

    if not username or not password:
        raise ValueError("SHOWDOWN_USERNAME and SHOWDOWN_PASSWORD required in .env")

    log_startup(f"Challenging {opponent} as {username}")

    player = GeminiPlayer(
        account_configuration=AccountConfiguration(username, password),
        server_configuration=ShowdownServerConfiguration,
        battle_format=BATTLE_FORMAT,
        max_concurrent_battles=1,
    )

    await forfeit_on_cancel(player, player.send_challenges(opponent, n_challenges=1))


async def ladder(n_games: int = 5):
    username = os.getenv("SHOWDOWN_USERNAME")
    password = os.getenv("SHOWDOWN_PASSWORD")

    if not username or not password:
        raise ValueError("SHOWDOWN_USERNAME and SHOWDOWN_PASSWORD required in .env")

    log_startup(f"Playing {n_games} ladder games as {username}")

    player = GeminiPlayer(
        account_configuration=AccountConfiguration(username, password),
        server_configuration=ShowdownServerConfiguration,
        battle_format=BATTLE_FORMAT,
        max_concurrent_battles=1,
        start_timer_on_battle_start=True,
    )

    await forfeit_on_cancel(player, player.ladder(n_games))

    log_results(
        player.n_won_battles,
        player.n_finished_battles,
        player.win_rate * 100 if player.n_finished_battles > 0 else 0,
    )


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
    python showdown.py --test -v           # Verbose logging
    python showdown.py --test --log-file battle.log  # Log to file
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
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose logging (show analysis, decision reasoning, agent calls)",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        help="Write verbose logs to a file (always captures full detail)",
    )

    args = parser.parse_args()

    set_log_level(VERBOSE if args.verbose else MINIMAL)
    if args.log_file:
        set_log_file(args.log_file)

    check_api_key()

    log_info("Press Ctrl+C during a battle to resign and exit")

    if args.test:
        asyncio.run(test_locally(args.num_battles))
    elif args.online:
        asyncio.run(play_online())
    elif args.challenge:
        asyncio.run(challenge_player(args.challenge))
    elif args.ladder:
        asyncio.run(ladder(args.num_battles))
    else:
        log_info("No mode specified, running local test...")
        asyncio.run(test_locally(args.num_battles))

    log_token_summary()
    close_log_file()


if __name__ == "__main__":
    main()
