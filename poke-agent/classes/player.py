"""
GeminiPlayer - AI Pokemon Battle Player

A poke-env Player that uses LangGraph agents powered by Google Gemini
to make competitive Pokemon battle decisions.

Architecture:
    AnalysisAgent (Researcher) -> DecisionAgent (Captain) -> BattleAgent (Executor)

    HistoryAgent runs after each turn to maintain battle context.
"""

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
    Pokemon battle player powered by LangGraph agents using Google Gemini.

    The player uses a multi-agent architecture:
    - AnalysisAgent: Gathers battle state information
    - DecisionAgent: Makes strategic decisions
    - BattleAgent: Executes the decision
    - HistoryAgent: Maintains battle history context
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Shared state across agents
        self.state: SharedState = {
            "analysis": "",
            "decision": "",
            "history": [],
        }

        # Track battle observations for history
        self._last_battle_tag: Optional[str] = None

    def choose_move(self, battle: Battle) -> BattleOrder:
        """
        Choose a move using the multi-agent system.

        This method is called by poke-env whenever a decision is needed.
        It orchestrates the agent pipeline and returns a BattleOrder.
        """
        print(f"\n[bold cyan]{'=' * 60}[/bold cyan]")
        print(
            f"[bold cyan]Turn {battle.turn} - {battle.active_pokemon.species if battle.active_pokemon else 'Unknown'} vs {battle.opponent_active_pokemon.species if battle.opponent_active_pokemon else 'Unknown'}[/bold cyan]"
        )
        print(f"[bold cyan]{'=' * 60}[/bold cyan]\n")

        try:
            # Create toolkit with current battle state
            toolkit = AgentToolkit(battle)

            # Phase 1: Analysis
            print("[bold green]Phase 1: Analysis[/bold green]")
            analysis_agent = AnalysisAgent(battle, toolkit)
            self.state = analysis_agent.execute_agent(self.state)

            # Phase 2: Decision
            print("\n[bold green]Phase 2: Decision[/bold green]")
            decision_agent = DecisionAgent()
            self.state = decision_agent.execute_agent(self.state)

            # Phase 3: Battle (Execute)
            print("\n[bold green]Phase 3: Battle Execution[/bold green]")
            battle_agent = BattleAgent(battle)
            order = battle_agent.execute_agent(self.state)

            # If we got an order, return it
            if order:
                print(f"\n[bold green]Executing order: {order.message}[/bold green]\n")
                return order

            # Fallback to random move if something went wrong
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
        """Handle forced switch situations."""
        # For forced switches, we still want strategic decision making
        # but we can simplify since we can only switch
        if battle.available_switches:
            # Use a simpler heuristic for forced switches
            # TODO: Could enhance this with agent-based switching
            return self.choose_random_move(battle)

        return self.choose_random_move(battle)

    def teampreview(self, battle: Battle) -> str:
        """
        Handle team preview phase.

        For now, use random order. This could be enhanced with
        agent-based team ordering in the future.
        """
        # TODO: Add agent-based teampreview logic
        return self.random_teampreview(battle)

    def battle_callback(self, battle: Battle) -> None:
        """
        Called after each battle message is processed.

        Use this to update history with battle observations.
        """
        # Process history for completed turns
        # This could be enhanced to capture battle log snippets
        pass

    def reset_state(self) -> None:
        """Reset state for a new battle."""
        self.state = {
            "analysis": "",
            "decision": "",
            "history": [],
        }
        self._last_battle_tag = None
