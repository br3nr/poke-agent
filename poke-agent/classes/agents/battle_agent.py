"""
BattleAgent - The Team Battler

Executes the decision made by the DecisionAgent.
Translates the captain's instructions into a poke-env BattleOrder.

This agent parses the decision text directly without needing an LLM,
since the DecisionAgent outputs structured commands like:
- "USE MOVE: <move_name>"
- "SWITCH TO: <pokemon_name>"
"""

import re
from rich import print
from typing import Optional

from poke_env.battle import Battle
from poke_env.player import Player
from poke_env.player.battle_order import BattleOrder

from classes.sharedstate import SharedState
from classes.agent_toolkit import print_agent_function_call


class BattleAgent:
    def __init__(self, battle: Battle):
        self.battle = battle
        self.selected_order: Optional[BattleOrder] = None

    def execute_agent(self, state: SharedState) -> Optional[BattleOrder]:
        """Parse the decision and create a battle order."""
        decision = state.get("decision", "")

        # Try to parse "USE MOVE: <move_name>"
        move_match = re.search(r"USE MOVE:\s*(\w+)", decision, re.IGNORECASE)
        if move_match:
            move_name = move_match.group(1)
            self._choose_move(move_name)
            return self.selected_order

        # Try to parse "SWITCH TO: <pokemon_name>"
        switch_match = re.search(r"SWITCH TO:\s*(\w+)", decision, re.IGNORECASE)
        if switch_match:
            pokemon_name = switch_match.group(1)
            self._swap_pokemon(pokemon_name)
            return self.selected_order

        # Fallback: try to find any move name mentioned
        print(
            "[bold yellow]Could not parse decision, attempting fallback...[/bold yellow]"
        )
        for move in self.battle.available_moves:
            if move.id.lower() in decision.lower():
                self._choose_move(move.id)
                return self.selected_order

        # Last resort: use first available move
        if self.battle.available_moves:
            fallback_move = self.battle.available_moves[0]
            print(f"[bold yellow]Using fallback move: {fallback_move.id}[/bold yellow]")
            self.selected_order = Player.create_order(fallback_move)
            return self.selected_order

        # If no moves, try to switch
        if self.battle.available_switches:
            fallback_pokemon = self.battle.available_switches[0]
            print(
                f"[bold yellow]Using fallback switch: {fallback_pokemon.species}[/bold yellow]"
            )
            self.selected_order = Player.create_order(fallback_pokemon)
            return self.selected_order

        return None

    def _choose_move(self, move_name: str) -> str:
        """Select a move to use in battle."""
        print_agent_function_call("choose_move", move_name)

        # Normalize move name for comparison
        normalized_input = self._normalize_name(move_name)

        # Find the move in available moves
        for move in self.battle.available_moves:
            if self._normalize_name(move.id) == normalized_input:
                self.selected_order = Player.create_order(move)
                print(
                    f"[bold bright_red]Battle Agent: Selected move {move.id}[/bold bright_red]"
                )
                return f"Selected move: {move.id}"

        # If exact match not found, try partial match
        for move in self.battle.available_moves:
            if (
                normalized_input in self._normalize_name(move.id)
                or self._normalize_name(move.id) in normalized_input
            ):
                self.selected_order = Player.create_order(move)
                print(
                    f"[bold bright_red]Battle Agent: Selected move {move.id}[/bold bright_red]"
                )
                return f"Selected move: {move.id}"

        # Fallback: use first available move
        if self.battle.available_moves:
            fallback_move = self.battle.available_moves[0]
            self.selected_order = Player.create_order(fallback_move)
            print(
                f"[bold bright_red]Battle Agent: Move '{move_name}' not found, using fallback: {fallback_move.id}[/bold bright_red]"
            )
            return f"Move '{move_name}' not found, using fallback: {fallback_move.id}"

        return f"No moves available"

    def _swap_pokemon(self, pokemon_name: str) -> str:
        """Switch to a different pokemon."""
        print_agent_function_call("swap_pokemon", pokemon_name)

        # Normalize pokemon name for comparison
        normalized_input = self._normalize_name(pokemon_name)

        # Find the pokemon in available switches
        for pokemon in self.battle.available_switches:
            if self._normalize_name(pokemon.species) == normalized_input:
                self.selected_order = Player.create_order(pokemon)
                print(
                    f"[bold bright_red]Battle Agent: Switching to {pokemon.species}[/bold bright_red]"
                )
                return f"Switching to: {pokemon.species}"

        # Try partial match
        for pokemon in self.battle.available_switches:
            if (
                normalized_input in self._normalize_name(pokemon.species)
                or self._normalize_name(pokemon.species) in normalized_input
            ):
                self.selected_order = Player.create_order(pokemon)
                print(
                    f"[bold bright_red]Battle Agent: Switching to {pokemon.species}[/bold bright_red]"
                )
                return f"Switching to: {pokemon.species}"

        # Fallback: switch to first available
        if self.battle.available_switches:
            fallback_pokemon = self.battle.available_switches[0]
            self.selected_order = Player.create_order(fallback_pokemon)
            print(
                f"[bold bright_red]Battle Agent: Pokemon '{pokemon_name}' not found, switching to: {fallback_pokemon.species}[/bold bright_red]"
            )
            return f"Pokemon '{pokemon_name}' not found, switching to: {fallback_pokemon.species}"

        return f"No switches available"

    def _normalize_name(self, name: str) -> str:
        """Normalize name for comparison."""
        return (
            name.lower()
            .replace(" ", "")
            .replace("-", "")
            .replace("_", "")
            .replace("'", "")
        )

    def get_order(self) -> Optional[BattleOrder]:
        """Get the battle order that was selected."""
        return self.selected_order
