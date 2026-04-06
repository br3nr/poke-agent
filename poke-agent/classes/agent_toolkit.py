from typing import List, Dict, Any, Optional
from poke_env.battle import Battle, Pokemon, Move, PokemonType
from poke_env.data import GenData
from rich import print


def print_agent_function_call(fn_name: str, fn_input: str, fn_output: Any = "N/A"):
    print(
        f"[bold blue]\nPoke Agent Triggered: {fn_name}\nInput: {fn_input}\nOutput:{fn_output}\n[/bold blue]"
    )


class AgentToolkit:
    def __init__(self, battle: Battle):
        self.battle = battle
        self.gen_data = GenData.from_gen(battle.gen)

    def get_pokemon_details(self, pokemon_name: str) -> str:
        """Gets the details about one of the pokemon in your team."""
        for pokemon in self.battle.team.values():
            if self._normalize_name(pokemon.species) == self._normalize_name(
                pokemon_name
            ):
                details = self._format_pokemon_details(pokemon)
                return details
        return f"Could not find pokemon '{pokemon_name}' in team"

    def get_opponent_pokemon_details(self, pokemon_name: str) -> str:
        """Gets the details about the opponent's pokemon including type advantages."""
        opponent_pokemon = None

        if self.battle.opponent_active_pokemon:
            active = self.battle.opponent_active_pokemon
            if self._normalize_name(active.species) == self._normalize_name(
                pokemon_name
            ):
                opponent_pokemon = active

        if not opponent_pokemon:
            for pokemon in self.battle.opponent_team.values():
                if self._normalize_name(pokemon.species) == self._normalize_name(
                    pokemon_name
                ):
                    opponent_pokemon = pokemon
                    break

        if not opponent_pokemon:
            return f"Could not find opponent pokemon '{pokemon_name}'"

        types = [t.name for t in opponent_pokemon.types if t]
        details = f"The opponent's {opponent_pokemon.species} is a {' and '.join(types)} type pokemon."
        details += f"\nHP: {opponent_pokemon.current_hp_fraction * 100:.0f}%"

        if opponent_pokemon.status:
            details += f"\nStatus: {opponent_pokemon.status.name}"

        details += f"\n\n{self.check_type_advantages(pokemon_name)}"

        return details

    def get_team_details(self, team_name: str = "team") -> List[dict]:
        """Returns all of the pokemon in the team with their current status."""
        team_list = []

        for pokemon in self.battle.team.values():
            if pokemon.fainted:
                status = "FAINTED"
            else:
                status = f"{pokemon.current_hp_fraction * 100:.0f}% HP"

            types = [t.name for t in pokemon.types if t]
            team_list.append(
                {
                    "name": pokemon.species,
                    "types": types,
                    "status": status,
                    "active": pokemon.active,
                }
            )

        return team_list

    def check_type_advantages(self, pokemon_name: str) -> str:
        """Takes the name of a pokemon. Returns what types the pokemon is weak/resistant to."""
        target_pokemon = None

        if self.battle.opponent_active_pokemon:
            if self._normalize_name(
                self.battle.opponent_active_pokemon.species
            ) == self._normalize_name(pokemon_name):
                target_pokemon = self.battle.opponent_active_pokemon

        if not target_pokemon:
            for pokemon in self.battle.opponent_team.values():
                if self._normalize_name(pokemon.species) == self._normalize_name(
                    pokemon_name
                ):
                    target_pokemon = pokemon
                    break

        if not target_pokemon:
            for pokemon in self.battle.team.values():
                if self._normalize_name(pokemon.species) == self._normalize_name(
                    pokemon_name
                ):
                    target_pokemon = pokemon
                    break

        if not target_pokemon:
            return f"Could not find pokemon '{pokemon_name}'"

        weaknesses = []
        resistances = []
        immunities = []

        for attacking_type in PokemonType:
            if attacking_type == PokemonType.THREE_QUESTION_MARKS:
                continue

            multiplier = target_pokemon.damage_multiplier(attacking_type)

            if multiplier == 0:
                immunities.append(attacking_type.name)
            elif multiplier >= 4:
                weaknesses.append(f"{attacking_type.name}*")  # 4x
            elif multiplier >= 2:
                weaknesses.append(attacking_type.name)
            elif multiplier <= 0.25:
                resistances.append(f"{attacking_type.name}*")  # 4x resist
            elif multiplier <= 0.5:
                resistances.append(attacking_type.name)

        relations = (
            f"Weaknesses: {', '.join(sorted(weaknesses)) if weaknesses else 'None'}\n"
            f"Resistances: {', '.join(sorted(resistances)) if resistances else 'None'}\n"
            f"Immunities: {', '.join(sorted(immunities)) if immunities else 'None'}"
        )

        return relations

    def get_current_moves(self) -> List[Dict[str, Any]]:
        """Gets the available moves for your active Pokemon."""
        detailed_moves = []

        for move in self.battle.available_moves:
            move_info = {
                "name": move.id,
                "type": move.type.name if move.type else "UNKNOWN",
                "category": move.category.name if move.category else "UNKNOWN",
                "accuracy": move.accuracy if move.accuracy else 100,
                "power": move.base_power,
                "priority": move.priority,
                "pp": move.current_pp,
            }
            detailed_moves.append(move_info)

        return detailed_moves

    def get_available_switches(self) -> List[Dict[str, Any]]:
        """Gets the available pokemon to switch to."""
        switches = []

        for pokemon in self.battle.available_switches:
            types = [t.name for t in pokemon.types if t]
            switches.append(
                {
                    "name": pokemon.species,
                    "types": types,
                    "hp": f"{pokemon.current_hp_fraction * 100:.0f}%",
                    "status": pokemon.status.name if pokemon.status else None,
                }
            )

        return switches

    def _format_pokemon_details(self, pokemon: Pokemon) -> str:
        types = [t.name for t in pokemon.types if t]

        details = [
            f"Name: {pokemon.species}",
            f"Types: {', '.join(types)}",
            f"HP: {pokemon.current_hp_fraction * 100:.0f}%",
            f"Active: {pokemon.active}",
        ]

        if pokemon.status:
            details.append(f"Status: {pokemon.status.name}")
        if pokemon.ability:
            details.append(f"Ability: {pokemon.ability}")
        if pokemon.item:
            details.append(f"Item: {pokemon.item}")
        if pokemon.moves:
            move_names = list(pokemon.moves.keys())
            details.append(f"Known Moves: {', '.join(move_names)}")
        if pokemon.stats:
            stats_str = ", ".join(f"{k}: {v}" for k, v in pokemon.stats.items() if v)
            if stats_str:
                details.append(f"Stats: {stats_str}")
        if any(v != 0 for v in pokemon.boosts.values()):
            boosts_str = ", ".join(
                f"{k}: {v:+d}" for k, v in pokemon.boosts.items() if v != 0
            )
            details.append(f"Boosts: {boosts_str}")

        return "\n".join(details)

    def _normalize_name(self, name: str) -> str:
        return name.lower().replace(" ", "").replace("-", "").replace("'", "")
