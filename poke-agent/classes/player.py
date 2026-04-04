from typing import List, Optional
from rich import print

from poke_env import Player
from poke_env.battle import Battle
from poke_env.player.battle_order import BattleOrder

from classes.agent_toolkit import AgentToolkit
from classes.agents.analysis_agent import AnalysisAgent
from classes.agents.decision_agent import DecisionAgent
from classes.agents.battle_agent import BattleAgent
from classes.agents.history_agent import HistoryAgent
from classes.sharedstate import SharedState


class GeminiPlayer(Player):
    """
    AnalysisAgent (Researcher) -> DecisionAgent (Captain) -> BattleAgent (Executor)
    HistoryAgent runs after each turn to maintain battle context.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state: SharedState = {
            "analysis": "",
            "decision": "",
            "history": [],
        }
        self._last_battle_tag: Optional[str] = None

    def choose_move(self, battle: Battle) -> BattleOrder:
        print(f"\n[bold cyan]{'=' * 60}[/bold cyan]")
        print(
            f"[bold cyan]Turn {battle.turn} - {battle.active_pokemon.species if battle.active_pokemon else 'Unknown'} vs {battle.opponent_active_pokemon.species if battle.opponent_active_pokemon else 'Unknown'}[/bold cyan]"
        )
        print(f"[bold cyan]{'=' * 60}[/bold cyan]\n")

        try:
            toolkit = AgentToolkit(battle)

            print("[bold green]Phase 1: Analysis[/bold green]")
            analysis_agent = AnalysisAgent(battle, toolkit)
            self.state = analysis_agent.execute_agent(self.state)

            print("\n[bold green]Phase 2: Decision[/bold green]")
            decision_agent = DecisionAgent()
            self.state = decision_agent.execute_agent(self.state)

            print("\n[bold green]Phase 3: Battle Execution[/bold green]")
            battle_agent = BattleAgent(battle)
            order = battle_agent.execute_agent(self.state)

            if order:
                print(f"\n[bold green]Executing order: {order.message}[/bold green]\n")
                return order

            print(
                "[bold yellow]Warning: No order from BattleAgent, using random move[/bold yellow]"
            )
            return self.choose_random_move(battle)

        except Exception as e:
            print(f"[bold red]Error in agent pipeline: {e}[/bold red]")
            import traceback

            traceback.print_exc()
            return self.choose_random_move(battle)

    def _pokemon_to_switchin_pokemon(self, battle: Battle) -> BattleOrder:
        # TODO: could enhance with agent-based switching
        if battle.available_switches:
            return self.choose_random_move(battle)
        return self.choose_random_move(battle)

    def teampreview(self, battle: Battle) -> str:
        # TODO: add agent-based teampreview logic
        return self.random_teampreview(battle)

    def battle_callback(self, battle: Battle) -> None:
        pass

    def reset_state(self) -> None:
        self.state = {
            "analysis": "",
            "decision": "",
            "history": [],
        }
        self._last_battle_tag = None
