import re
from rich import print
from typing import Optional

from poke_env.battle import Battle
from poke_env.player import Player
from poke_env.player.battle_order import BattleOrder

from classes.sharedstate import SharedState
from classes.agent_toolkit import print_agent_function_call


class BattleAgent:
    """
    Parses decision text for commands:
    - "USE MOVE: <move_name>"
    - "SWITCH TO: <pokemon_name>"
    """

    def __init__(self, battle: Battle):
        self.battle = battle
        self.selected_order: Optional[BattleOrder] = None

    def execute_agent(self, state: SharedState) -> Optional[BattleOrder]:
        decision = state.get("decision", "")

        move_match = re.search(r"USE MOVE:\s*(\w+)", decision, re.IGNORECASE)
        if move_match:
            move_name = move_match.group(1)
            self._choose_move(move_name)
            return self.selected_order

        switch_match = re.search(r"SWITCH TO:\s*(\w+)", decision, re.IGNORECASE)
        if switch_match:
            pokemon_name = switch_match.group(1)
            self._swap_pokemon(pokemon_name)
            return self.selected_order

        # fallback: try to find any move name mentioned
        print(
            "[bold yellow]Could not parse decision, attempting fallback...[/bold yellow]"
        )
        for move in self.battle.available_moves:
            if move.id.lower() in decision.lower():
                self._choose_move(move.id)
                return self.selected_order

        if self.battle.available_moves:
            fallback_move = self.battle.available_moves[0]
            print(f"[bold yellow]Using fallback move: {fallback_move.id}[/bold yellow]")
            self.selected_order = Player.create_order(fallback_move)
            return self.selected_order

        if self.battle.available_switches:
            fallback_pokemon = self.battle.available_switches[0]
            print(
                f"[bold yellow]Using fallback switch: {fallback_pokemon.species}[/bold yellow]"
            )
            self.selected_order = Player.create_order(fallback_pokemon)
            return self.selected_order

        return None

    def _choose_move(self, move_name: str) -> str:
        print_agent_function_call("choose_move", move_name)
        normalized_input = self._normalize_name(move_name)

        for move in self.battle.available_moves:
            if self._normalize_name(move.id) == normalized_input:
                self.selected_order = Player.create_order(move)
                print(
                    f"[bold bright_red]Battle Agent: Selected move {move.id}[/bold bright_red]"
                )
                return f"Selected move: {move.id}"

        # partial match
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

        if self.battle.available_moves:
            fallback_move = self.battle.available_moves[0]
            self.selected_order = Player.create_order(fallback_move)
            print(
                f"[bold bright_red]Battle Agent: Move '{move_name}' not found, using fallback: {fallback_move.id}[/bold bright_red]"
            )
            return f"Move '{move_name}' not found, using fallback: {fallback_move.id}"

        return "No moves available"

    def _swap_pokemon(self, pokemon_name: str) -> str:
        print_agent_function_call("swap_pokemon", pokemon_name)
        normalized_input = self._normalize_name(pokemon_name)

        for pokemon in self.battle.available_switches:
            if self._normalize_name(pokemon.species) == normalized_input:
                self.selected_order = Player.create_order(pokemon)
                print(
                    f"[bold bright_red]Battle Agent: Switching to {pokemon.species}[/bold bright_red]"
                )
                return f"Switching to: {pokemon.species}"

        # partial match
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

        if self.battle.available_switches:
            fallback_pokemon = self.battle.available_switches[0]
            self.selected_order = Player.create_order(fallback_pokemon)
            print(
                f"[bold bright_red]Battle Agent: Pokemon '{pokemon_name}' not found, switching to: {fallback_pokemon.species}[/bold bright_red]"
            )
            return f"Pokemon '{pokemon_name}' not found, switching to: {fallback_pokemon.species}"

        return "No switches available"

    def _normalize_name(self, name: str) -> str:
        return (
            name.lower()
            .replace(" ", "")
            .replace("-", "")
            .replace("_", "")
            .replace("'", "")
        )

    def get_order(self) -> Optional[BattleOrder]:
        return self.selected_order
