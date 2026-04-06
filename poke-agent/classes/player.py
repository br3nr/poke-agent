from typing import Optional
from poke_env import Player
from poke_env.battle import Battle
from poke_env.player.battle_order import BattleOrder

from classes.battle_state import BattleStateBuilder
from classes.agents.analysis_agent import AnalysisAgent
from classes.agents.decision_agent import DecisionAgent
from classes.agents.battle_agent import BattleAgent
from classes.sharedstate import SharedState
from utils.logging import (
    log_turn_header,
    log_phase,
    log_analysis,
    log_order,
    log_warning,
    log_error,
    log_battle_start,
    log_battle_end,
)


class GeminiPlayer(Player):
    """
    AnalysisAgent (Researcher) -> DecisionAgent (Captain) -> BattleAgent (Executor)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state: SharedState = {
            "analysis": "",
            "decision": "",
        }
        self._last_battle_tag: Optional[str] = None
        self._pre_battle_ratings: dict = {}  # battle_tag -> your_rating

    def choose_move(self, battle: Battle) -> BattleOrder:
        # log battle start on first turn of a new battle
        if battle.battle_tag != self._last_battle_tag:
            self._last_battle_tag = battle.battle_tag
            your_rating, opp_rating = self._get_pre_battle_ratings(battle)
            if your_rating is not None:
                self._pre_battle_ratings[battle.battle_tag] = your_rating
            opponent = battle.opponent_username or "Unknown"
            log_battle_start(opponent, your_rating, opp_rating)

        your_mon = battle.active_pokemon.species if battle.active_pokemon else "Unknown"
        opp_mon = (
            battle.opponent_active_pokemon.species
            if battle.opponent_active_pokemon
            else "Unknown"
        )
        log_turn_header(battle.turn, your_mon, opp_mon)

        try:
            self.state["analysis"] = ""
            self.state["decision"] = ""

            state_builder = BattleStateBuilder(battle)

            log_phase(1, "Analysis")
            analysis_agent = AnalysisAgent(battle, state_builder)
            self.state = analysis_agent.execute_agent(self.state)
            log_analysis(self.state["analysis"])

            log_phase(2, "Decision")
            decision_agent = DecisionAgent()
            self.state = decision_agent.execute_agent(self.state)

            log_phase(3, "Battle Execution")
            battle_agent = BattleAgent(battle)
            order = battle_agent.execute_agent(self.state)

            if order:
                log_order(order.message)
                return order

            log_warning("No order from agents, using random move")
            return self.choose_random_move(battle)

        except Exception as e:
            log_error(f"Agent pipeline error: {e}")
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

    def _battle_finished_callback(self, battle) -> None:
        """Called by poke-env when a battle ends. Log ELO summary."""
        opponent = battle.opponent_username or "Unknown"
        won = battle.won if battle.won is not None else False

        your_rating = battle.rating
        opp_rating = battle.opponent_rating

        # calculate ELO change if we have pre-battle rating
        rating_change = None
        pre_rating = self._pre_battle_ratings.pop(battle.battle_tag, None)
        if pre_rating is not None and your_rating is not None:
            rating_change = your_rating - pre_rating

        log_battle_end(won, opponent, your_rating, opp_rating, rating_change)

    def _get_pre_battle_ratings(self, battle: Battle):
        """Extract pre-battle ratings from the |player| protocol messages."""
        your_rating = None
        opp_rating = None

        for player_info in battle._players:
            rating = player_info.get("rating")
            if rating is not None:
                try:
                    rating = int(rating)
                except (ValueError, TypeError):
                    rating = None

            username = player_info.get("username", "")
            if username == battle.player_username:
                your_rating = rating
            else:
                opp_rating = rating

        return your_rating, opp_rating

    async def forfeit_active_battles(self) -> None:
        """Forfeit all unfinished battles."""
        from utils.logging import log_warning, log_info

        for battle in self._battles.values():
            if not battle.finished:
                log_warning(f"Forfeiting battle: {battle.battle_tag}")
                try:
                    await self.ps_client.send_message("/forfeit", battle.battle_tag)
                except Exception as e:
                    log_error(f"Failed to forfeit {battle.battle_tag}: {e}")

    def reset_state(self) -> None:
        self.state = {
            "analysis": "",
            "decision": "",
        }
        self._last_battle_tag = None
