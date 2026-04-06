from typing import List, Dict, Any
from poke_env.battle import (
    Battle,
    Pokemon,
    PokemonType,
    Weather,
    Field,
    SideCondition,
    Effect,
)
from poke_env.data import GenData

from utils.logging import print_agent_function_call


class BattleStateBuilder:
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
                print_agent_function_call("get_pokemon_details", pokemon_name, details)
                return details
        return f"Could not find pokemon '{pokemon_name}' in team"

    def get_opponent_pokemon_details(self, pokemon_name: str) -> str:
        """Gets the details about the opponent's active pokemon including type advantages."""
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

        if opponent_pokemon.ability:
            details += f"\nAbility: {opponent_pokemon.ability}"

        if opponent_pokemon.item and opponent_pokemon.item != "unknown_item":
            details += f"\nItem: {opponent_pokemon.item}"

        if opponent_pokemon.moves:
            move_strs = []
            for move_id, move in opponent_pokemon.moves.items():
                move_type = move.type.name if move.type else "UNKNOWN"
                category = move.category.name if move.category else "UNKNOWN"
                move_strs.append(
                    f"{move_id} ({move_type}, {category}, Power: {move.base_power})"
                )
            details += f"\nKnown Moves: {', '.join(move_strs)}"

        if any(v != 0 for v in opponent_pokemon.boosts.values()):
            boosts_str = ", ".join(
                f"{k}: {v:+d}" for k, v in opponent_pokemon.boosts.items() if v != 0
            )
            details += f"\nStat Changes: {boosts_str}"

        if opponent_pokemon.effects:
            effect_names = [
                e.name for e in opponent_pokemon.effects if e != Effect.UNKNOWN
            ]
            if effect_names:
                details += f"\nActive Effects: {', '.join(effect_names)}"

        if opponent_pokemon.is_terastallized:
            tera_type = opponent_pokemon.tera_type
            details += f"\nTerastallized: {tera_type.name if tera_type else 'YES'}"

        if opponent_pokemon.last_move:
            details += f"\nLast Move Used: {opponent_pokemon.last_move.id}"

        details += f"\n\n{self.check_type_advantages(pokemon_name)}"

        print_agent_function_call("get_opponent_pokemon_details", pokemon_name, details)
        return details

    def get_opponent_revealed_team(self) -> List[Dict[str, Any]]:
        """Returns all revealed opponent pokemon that are not currently active."""
        revealed = []

        for pokemon in self.battle.opponent_team.values():
            if pokemon.active:
                continue

            types = [t.name for t in pokemon.types if t]
            known_moves = []
            for move_id, move in pokemon.moves.items():
                known_moves.append(
                    {
                        "name": move_id,
                        "type": move.type.name if move.type else "UNKNOWN",
                        "category": move.category.name if move.category else "UNKNOWN",
                        "power": move.base_power,
                    }
                )

            entry = {
                "name": pokemon.species,
                "types": types,
                "hp": f"{pokemon.current_hp_fraction * 100:.0f}%",
                "fainted": pokemon.fainted,
                "status": pokemon.status.name if pokemon.status else None,
                "known_moves": known_moves,
                "ability": pokemon.ability,
                "item": pokemon.item if pokemon.item != "unknown_item" else None,
            }
            revealed.append(entry)

        print_agent_function_call("get_opponent_revealed_team", "opponent", revealed)
        return revealed

    def get_team_details(self) -> List[Dict[str, Any]]:
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

        print_agent_function_call("get_team_details", "team", team_list)
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
                weaknesses.append(f"{attacking_type.name} (4x)")
            elif multiplier >= 2:
                weaknesses.append(attacking_type.name)
            elif multiplier <= 0.25:
                resistances.append(f"{attacking_type.name} (4x resist)")
            elif multiplier <= 0.5:
                resistances.append(attacking_type.name)

        relations = (
            f"Weaknesses: {', '.join(sorted(weaknesses)) if weaknesses else 'None'}\n"
            f"Resistances: {', '.join(sorted(resistances)) if resistances else 'None'}\n"
            f"Immunities: {', '.join(sorted(immunities)) if immunities else 'None'}"
        )

        print_agent_function_call("check_type_advantages", pokemon_name, relations)
        return relations

    def get_field_conditions(self) -> str:
        """Returns current battlefield conditions: weather, terrain, trick room, side conditions."""
        sections = []

        # weather
        if self.battle.weather:
            for weather, turn in self.battle.weather.items():
                if weather != Weather.UNKNOWN:
                    sections.append(f"Weather: {weather.name}")

        # field effects (terrain, trick room, gravity, etc.)
        if self.battle.fields:
            for field, turn in self.battle.fields.items():
                if field != Field.UNKNOWN:
                    sections.append(f"Field: {field.name}")

        # conditions
        our_conditions = []
        if self.battle.side_conditions:
            for condition, value in self.battle.side_conditions.items():
                if condition != SideCondition.UNKNOWN:
                    label = condition.name
                    if condition in (SideCondition.SPIKES, SideCondition.TOXIC_SPIKES):
                        label += f" (x{value})"
                    our_conditions.append(label)
        if our_conditions:
            sections.append(f"Your side: {', '.join(our_conditions)}")

        # opponent conditions
        opp_conditions = []
        if self.battle.opponent_side_conditions:
            for condition, value in self.battle.opponent_side_conditions.items():
                if condition != SideCondition.UNKNOWN:
                    label = condition.name
                    if condition in (SideCondition.SPIKES, SideCondition.TOXIC_SPIKES):
                        label += f" (x{value})"
                    opp_conditions.append(label)
        if opp_conditions:
            sections.append(f"Opponent's side: {', '.join(opp_conditions)}")

        if not sections:
            return "No active field conditions"

        result = "\n".join(sections)
        print_agent_function_call("get_field_conditions", "battle", result)
        return result

    def get_current_moves(self) -> List[Dict[str, Any]]:
        """Gets the available moves for your active Pokemon, including effectiveness vs the opponent."""
        detailed_moves = []
        opponent = self.battle.opponent_active_pokemon

        for move in self.battle.available_moves:
            move_info = {
                "name": move.id,
                "type": move.type.name if move.type else "UNKNOWN",
                "category": move.category.name if move.category else "UNKNOWN",
                "accuracy": f"{int(move.accuracy * 100)}%" if move.accuracy else "100%",
                "power": move.base_power,
                "priority": move.priority,
                "pp": move.current_pp,
            }

            if opponent and move.base_power > 0:
                multiplier = opponent.damage_multiplier(move)
                move_info["effectiveness"] = self._effectiveness_label(multiplier)

            detailed_moves.append(move_info)

        print_agent_function_call("get_current_moves", "active_pokemon", detailed_moves)
        return detailed_moves

    @staticmethod
    def _effectiveness_label(multiplier: float) -> str:
        if multiplier == 0:
            return "0x (immune)"
        elif multiplier <= 0.25:
            return f"{multiplier}x (doubly resisted)"
        elif multiplier <= 0.5:
            return f"{multiplier}x (resisted)"
        elif multiplier >= 4:
            return f"{multiplier}x (doubly super effective)"
        elif multiplier >= 2:
            return f"{multiplier}x (super effective)"
        else:
            return f"{multiplier}x (neutral)"

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

        print_agent_function_call("get_available_switches", "team", switches)
        return switches

    def get_turn_history(self, n: int = 5) -> str:
        """Returns a readable summary of the last n turns parsed from battle replay data."""
        replay_data = self.battle._replay_data
        if not replay_data:
            return "No turn history available yet."

        player_role = self.battle.player_role  # "p1" or "p2"

        # Split replay_data into per-turn chunks using "turn" markers
        turns: Dict[int, list] = {}
        current_turn = 0
        for event in replay_data:
            if len(event) >= 3 and event[1] == "turn":
                current_turn = int(event[2])
                turns.setdefault(current_turn, [])
            elif current_turn > 0:
                turns.setdefault(current_turn, []).append(event)

        if not turns:
            return "No turn history available yet."

        sorted_turn_nums = sorted(turns.keys())
        recent_turns = sorted_turn_nums[-n:]

        turn_summaries = []
        for turn_num in recent_turns:
            events = turns[turn_num]
            lines = self._parse_turn_events(events, player_role)

            if lines:
                turn_summaries.append(f"Turn {turn_num}:\n" + "\n".join(lines))

        if not turn_summaries:
            return "No turn history available yet."

        result = "\n\n".join(turn_summaries)
        print_agent_function_call("get_turn_history", f"last {n} turns", result)
        return result

    def _parse_turn_events(self, events: list, player_role: str) -> List[str]:
        """Parse a list of raw protocol events into readable lines."""
        lines = []

        for event in events:
            if len(event) < 2:
                continue

            event_type = event[1] if event[0] == "" else event[0]

            if event_type == "move":
                if len(event) >= 4:
                    user = self._format_actor(event[2], player_role)
                    move_name = event[3]
                    target = (
                        self._format_actor(event[4], player_role)
                        if len(event) >= 5
                        else ""
                    )
                    line = f"  {user} used {move_name}"
                    if target and target != user:
                        line += f" on {target}"
                    lines.append(line)

            elif event_type in ("switch", "drag"):
                if len(event) >= 4:
                    actor = self._format_actor(event[2], player_role)
                    species = event[3].split(",")[0]
                    verb = "switched in" if event_type == "switch" else "was dragged in"
                    lines.append(f"  {actor} {verb} ({species})")

            elif event_type == "-damage":
                if len(event) >= 4:
                    target = self._format_actor(event[2], player_role)
                    hp = event[3].split("/")[0] if "/" in event[3] else event[3]
                    source = ""
                    for part in event[4:]:
                        if part.startswith("[from]"):
                            source = f" from {part.replace('[from] ', '')}"
                    lines.append(f"  {target} took damage ({hp} HP remaining){source}")

            elif event_type == "-heal":
                if len(event) >= 4:
                    target = self._format_actor(event[2], player_role)
                    source = ""
                    for part in event[4:]:
                        if part.startswith("[from]"):
                            source = f" from {part.replace('[from] ', '')}"
                    lines.append(f"  {target} healed{source}")

            elif event_type == "-boost":
                if len(event) >= 5:
                    target = self._format_actor(event[2], player_role)
                    stat = event[3]
                    amount = event[4]
                    lines.append(f"  {target} gained +{amount} {stat}")

            elif event_type == "-unboost":
                if len(event) >= 5:
                    target = self._format_actor(event[2], player_role)
                    stat = event[3]
                    amount = event[4]
                    lines.append(f"  {target} lost -{amount} {stat}")

            elif event_type == "-status":
                if len(event) >= 4:
                    target = self._format_actor(event[2], player_role)
                    status = event[3]
                    lines.append(f"  {target} was inflicted with {status}")

            elif event_type == "-curestatus":
                if len(event) >= 4:
                    target = self._format_actor(event[2], player_role)
                    status = event[3]
                    lines.append(f"  {target} was cured of {status}")

            elif event_type == "faint":
                if len(event) >= 3:
                    target = self._format_actor(event[2], player_role)
                    lines.append(f"  {target} fainted")

            elif event_type == "-ability":
                if len(event) >= 4:
                    actor = self._format_actor(event[2], player_role)
                    ability = event[3]
                    lines.append(f"  {actor}'s ability {ability} activated")

            elif event_type == "-enditem":
                if len(event) >= 4:
                    actor = self._format_actor(event[2], player_role)
                    item = event[3]
                    lines.append(f"  {actor}'s {item} was consumed")

            elif event_type == "-weather":
                if len(event) >= 3:
                    weather = event[2]
                    if weather == "none":
                        lines.append("  Weather cleared")
                    else:
                        upkeep = any(p == "[upkeep]" for p in event[3:])
                        if not upkeep:
                            lines.append(f"  Weather changed to {weather}")

            elif event_type in ("-fieldstart", "-fieldend"):
                if len(event) >= 3:
                    field_name = event[2].replace("move: ", "")
                    verb = "started" if event_type == "-fieldstart" else "ended"
                    lines.append(f"  Field effect {field_name} {verb}")

            elif event_type in ("-sidestart", "-sideend"):
                if len(event) >= 4:
                    side = "Your" if event[2].startswith(player_role) else "Opponent's"
                    condition = event[3].replace("move: ", "")
                    verb = "set" if event_type == "-sidestart" else "removed"
                    lines.append(f"  {side} side: {condition} {verb}")

            elif event_type == "-terastallize":
                if len(event) >= 4:
                    actor = self._format_actor(event[2], player_role)
                    tera_type = event[3]
                    lines.append(f"  {actor} terastallized to {tera_type}")

            elif event_type == "-activate":
                if len(event) >= 4:
                    actor = self._format_actor(event[2], player_role)
                    effect = event[3].replace("move: ", "").replace("ability: ", "")
                    lines.append(f"  {actor}: {effect} activated")

        return lines

    def _format_actor(self, raw: str, player_role: str) -> str:
        """Converts 'p1a: Pikachu' to 'Your Pikachu' or 'Opponent's Pikachu'."""
        if ":" not in raw:
            return raw
        side, name = raw.split(": ", 1)
        if side.startswith(player_role):
            return f"Your {name}"
        else:
            return f"Opponent's {name}"

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

        if pokemon.effects:
            effect_names = [e.name for e in pokemon.effects if e != Effect.UNKNOWN]
            if effect_names:
                details.append(f"Active Effects: {', '.join(effect_names)}")

        if pokemon.is_terastallized:
            tera_type = pokemon.tera_type
            details.append(f"Terastallized: {tera_type.name if tera_type else 'YES'}")
        elif pokemon.tera_type:
            details.append(f"Tera Type: {pokemon.tera_type.name}")

        return "\n".join(details)

    def _normalize_name(self, name: str) -> str:
        return name.lower().replace(" ", "").replace("-", "").replace("'", "")
