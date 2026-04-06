from rich import print

from poke_env.battle import Battle

from classes.battle_state import BattleStateBuilder
from classes.sharedstate import SharedState


class AnalysisAgent:
    def __init__(self, battle: Battle, state_builder: BattleStateBuilder):
        self.battle = battle
        self.state_builder = state_builder

    def get_analysis(self, state: SharedState):
        active = self.battle.active_pokemon
        opponent = self.battle.opponent_active_pokemon

        active_name = active.species if active else "Unknown"
        opponent_name = opponent.species if opponent else "Unknown"

        sections = []

        sections.append("=== YOUR ACTIVE POKEMON ===")
        sections.append(self.state_builder.get_pokemon_details(active_name))

        sections.append("=== YOUR POKEMON'S TYPE DEFENSES ===")
        sections.append(self.state_builder.check_type_advantages(active_name))

        sections.append("=== AVAILABLE MOVES ===")
        moves = self.state_builder.get_current_moves()
        if moves:
            for m in moves:
                sections.append(
                    f"- {m['name']}: {m['type']} ({m['category']}) | "
                    f"Power: {m['power']} | Accuracy: {m['accuracy']} | "
                    f"Priority: {m['priority']} | PP: {m['pp']}"
                )
        else:
            sections.append("No moves available")

        sections.append("=== OPPONENT'S ACTIVE POKEMON ===")
        sections.append(self.state_builder.get_opponent_pokemon_details(opponent_name))

        sections.append("=== OPPONENT'S REVEALED TEAM ===")
        revealed = self.state_builder.get_opponent_revealed_team()
        if revealed:
            for p in revealed:
                status = " | FAINTED" if p["fainted"] else ""
                if p["status"]:
                    status += f" | {p['status']}"

                line = f"- {p['name']}: {', '.join(p['types'])} | HP: {p['hp']}{status}"

                if p["known_moves"]:
                    move_strs = [
                        f"{m['name']} ({m['type']}, {m['category']}, Power: {m['power']})"
                        for m in p["known_moves"]
                    ]
                    line += f"\n  Known Moves: {', '.join(move_strs)}"

                if p["ability"]:
                    line += f"\n  Ability: {p['ability']}"
                if p["item"]:
                    line += f"\n  Item: {p['item']}"

                sections.append(line)
        else:
            sections.append("No other opponent pokemon revealed yet")

        sections.append("=== YOUR TEAM ===")
        team = self.state_builder.get_team_details()

        for mon in team:
            if not mon["active"]:
                sections.append(
                    f"{mon['name']}\nTypes: {', '.join(mon['types'])}\nStatus: {mon['status']}"
                )

        sections.append("=== BATTLEFIELD CONDITIONS ===")
        sections.append(self.state_builder.get_field_conditions())

        # tera availability
        if self.battle.can_tera:
            active_tera = active.tera_type if active else None
            if active_tera:
                sections.append(
                    f"You can Terastallize to {active_tera.name} this turn."
                )
            else:
                sections.append("Terastallization is available this turn.")
        elif (
            hasattr(self.battle, "opponent_used_tera")
            and self.battle.opponent_used_tera
        ):
            sections.append("Opponent has already Terastallized.")

        # sections.append("=== AVAILABLE SWITCHES ===")
        # switches = self.state_builder.get_available_switches()
        # if switches:
        #     for s in switches:
        #         status = f" ({s['status']})" if s["status"] else ""
        #         sections.append(
        #             f"- {s['name']}: {', '.join(s['types'])} | HP: {s['hp']}{status}"
        #         )
        # else:
        #     sections.append("No switches available")

        analysis = "\n\n".join(sections)

        # print(f"[bold bright_yellow]Analysis Agent\n{analysis}[/bold bright_yellow]")

        state["analysis"] = analysis
        return state

    def execute_agent(self, state: SharedState):
        return self.get_analysis(state)
