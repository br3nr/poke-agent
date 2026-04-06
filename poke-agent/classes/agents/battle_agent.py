import re
from typing import Optional

from poke_env.battle import Battle
from poke_env.player import Player
from poke_env.player.battle_order import BattleOrder

from classes.sharedstate import SharedState
from utils.logging import log_battle_action, log_warning


class BattleAgent:
    """
    Parses decision text for commands:
    - "USE MOVE: <move_name>"
    - "SWITCH TO: <pokemon_name>"
    - "TERASTALLIZE AND USE MOVE: <move_name>"
    """

    def __init__(self, battle: Battle):
        self.battle = battle
        self.selected_order: Optional[BattleOrder] = None

    def execute_agent(self, state: SharedState) -> Optional[BattleOrder]:
        decision = state.get("decision", "")

        tera_move_match = re.search(
            r"TERASTALLIZE AND USE MOVE:\s*(.+)", decision, re.IGNORECASE
        )
        if tera_move_match:
            move_name = tera_move_match.group(1).strip()
            can_tera = self.battle.can_tera
            if not can_tera:
                log_warning(
                    "LLM requested tera but it's not available, using move without tera"
                )
            self._choose_move(move_name, terastallize=can_tera)
            return self.selected_order

        move_match = re.search(r"USE MOVE:\s*(.+)", decision, re.IGNORECASE)
        if move_match:
            move_name = move_match.group(1).strip()
            self._choose_move(move_name)
            return self.selected_order

        switch_match = re.search(r"SWITCH TO:\s*(.+)", decision, re.IGNORECASE)
        if switch_match:
            pokemon_name = switch_match.group(1).strip()
            self._swap_pokemon(pokemon_name)
            return self.selected_order

        # fallback: try to find any move name mentioned
        log_warning("Could not parse decision, attempting fallback")
        for move in self.battle.available_moves:
            if move.id.lower() in decision.lower():
                self._choose_move(move.id)
                return self.selected_order

        if self.battle.available_moves:
            fallback_move = self.battle.available_moves[0]
            log_battle_action("move", fallback_move.id, is_fallback=True)
            self.selected_order = Player.create_order(fallback_move)
            return self.selected_order

        if self.battle.available_switches:
            fallback_pokemon = self.battle.available_switches[0]
            log_battle_action("switch", fallback_pokemon.species, is_fallback=True)
            self.selected_order = Player.create_order(fallback_pokemon)
            return self.selected_order

        return None

    def _choose_move(self, move_name: str, terastallize: bool = False) -> str:
        normalized_input = self._normalize_name(move_name)

        for move in self.battle.available_moves:
            if self._normalize_name(move.id) == normalized_input:
                self.selected_order = Player.create_order(
                    move, terastallize=terastallize
                )
                action = f"tera + move" if terastallize else "move"
                log_battle_action(action, move.id)
                return f"Selected move: {move.id}"

        # partial match
        for move in self.battle.available_moves:
            if (
                normalized_input in self._normalize_name(move.id)
                or self._normalize_name(move.id) in normalized_input
            ):
                self.selected_order = Player.create_order(
                    move, terastallize=terastallize
                )
                action = f"tera + move" if terastallize else "move"
                log_battle_action(action, move.id)
                return f"Selected move: {move.id}"

        if self.battle.available_moves:
            fallback_move = self.battle.available_moves[0]
            self.selected_order = Player.create_order(fallback_move)
            log_battle_action("move", fallback_move.id, is_fallback=True)
            return f"Move '{move_name}' not found, using fallback: {fallback_move.id}"

        return "No moves available"

    def _swap_pokemon(self, pokemon_name: str) -> str:
        normalized_input = self._normalize_name(pokemon_name)

        for pokemon in self.battle.available_switches:
            if self._normalize_name(pokemon.species) == normalized_input:
                self.selected_order = Player.create_order(pokemon)
                log_battle_action("switch", pokemon.species)
                return f"Switching to: {pokemon.species}"

        # partial match
        for pokemon in self.battle.available_switches:
            if (
                normalized_input in self._normalize_name(pokemon.species)
                or self._normalize_name(pokemon.species) in normalized_input
            ):
                self.selected_order = Player.create_order(pokemon)
                log_battle_action("switch", pokemon.species)
                return f"Switching to: {pokemon.species}"

        if self.battle.available_switches:
            fallback_pokemon = self.battle.available_switches[0]
            self.selected_order = Player.create_order(fallback_pokemon)
            log_battle_action("switch", fallback_pokemon.species, is_fallback=True)
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
