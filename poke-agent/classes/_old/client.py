import asyncio
import websockets
import json
import re
import traceback
from json.decoder import JSONDecodeError
from rich import print
from typing import List, Dict, Optional

from classes.trainer import Trainer
from classes.agents.analysis_agent import AnalysisAgent
from classes.agents.decision_agent import DecisionAgent
from classes.agents.battle_agent import BattleAgent
from classes.pokemon import Pokemon
from classes.battle_data import BattleData
from classes.agents.history_agent import HistoryAgent
from classes.sharedstate import SharedState
from utils.helpers import get_challenge_data


class OpponentPokemon:
    def __init__(self, name: str, species: str, level: int, gender: Optional[str] = None,
                 hp_percentage: int = 100, status: Optional[str] = None, active: bool = False):
        self.name = name
        self.species = species
        self.level = level
        self.gender = gender
        self.hp_percentage = hp_percentage
        self.status = status
        self.active = active
        self.moves_seen = []
        self.ability = None
        self.item = None


class ShowdownClient:

    def __init__(self, username, password, opponent_name):
        self.username = username
        self.password = password
        self.opponent_name = opponent_name
        self.websocket = None
        self.battle_data = BattleData()
        self.opponent_team = {}

    async def showdown_client(self):
        headers = {"User-Agent": "PokeAgentv1"}
        url = "wss://sim3.psim.us/showdown/websocket"

        self.websocket = await websockets.connect(url, extra_headers=headers)
        state = SharedState(decision="", analysis="", history=[])

        while True:
            task = asyncio.wait_for(self.websocket.recv(), timeout=3000)
            message = await task
            print(message)
            if "challstr" in str(message):
                await self.authenticate(self.websocket, message)
                search_battle = f"|/challenge {self.opponent_name}, gen7randombattle"
                await self.websocket.send(search_battle)
            elif str(message).startswith(">battle"):
                await self.battle_loop(self.websocket, message, state)

    def parse_pokemon_details(self, details_string: str) -> Dict:
        parts = details_string.split(', ')
        species = parts[0]
        level = int(parts[1][1:])  # Remove 'L'
        gender = parts[2] if len(parts) > 2 and parts[2] in [
            'M', 'F'] else None

        return {'species': species, 'level': level, 'gender': gender}

    def parse_hp_condition(self, condition: str) -> Dict:
        if '/' in condition:
            hp_parts = condition.split('/')
            current_hp = int(hp_parts[0])
            parts = hp_parts[1].split(' ')
            max_hp = int(parts[0])
            status = parts[1] if len(parts) > 1 else None

            hp_percentage = int((current_hp / max_hp) * 100)
            return {
                'current_hp': current_hp,
                'max_hp': max_hp,
                'hp_percentage': hp_percentage,
                'status': status
            }
        else:
            return {'hp_percentage': 100, 'status': None}

    def process_battle_log(self, turn_stats):
        for line in turn_stats:
            line = line.strip()

            if line.startswith("|switch|p2a:"):
                self.parse_opponent_switch(line)
            elif line.startswith("|switch|p1a:"):
                self.parse_our_switch(line)
            elif line.startswith("|move|p2a:"):
                self.parse_opponent_move(line)
            elif line.startswith("|-damage|p2a:") or line.startswith("|-heal|p2a:"):
                self.parse_opponent_hp_change(line)
            elif line.startswith("|-ability|p2a:"):
                self.parse_opponent_ability(line)
            elif line.startswith("|-item|p2a:"):
                self.parse_opponent_item(line)
            elif line.startswith("|-status|p2a:"):
                self.parse_opponent_status(line)

    def parse_opponent_switch(self, line: str):
        try:
            parts = line.split('|')
            if len(parts) >= 4:
                pokemon_ident = parts[2]
                details = parts[3]
                condition = parts[4] if len(parts) > 4 else "100/100"

                pokemon_name = pokemon_ident.split(
                    ': ')[1] if ': ' in pokemon_ident else pokemon_ident.replace('p2a', '').strip()

                pokemon_details = self.parse_pokemon_details(details)
                hp_info = self.parse_hp_condition(condition)

                self.opponent_team[pokemon_ident] = OpponentPokemon(
                    name=pokemon_name,
                    species=pokemon_details['species'],
                    level=pokemon_details['level'],
                    gender=pokemon_details['gender'],
                    hp_percentage=hp_info['hp_percentage'],
                    status=hp_info.get('status'),
                    active=True
                )

                # set others inactive
                for ident, pokemon in self.opponent_team.items():
                    if ident != pokemon_ident:
                        pokemon.active = False

                print(
                    f"Opponent: {pokemon_name} (Lv.{pokemon_details['level']}, HP: {hp_info['hp_percentage']}%)")

                if hasattr(self.battle_data, 'opponent'):
                    self.battle_data.opponent.active_pokemon = pokemon_name

        except Exception as e:
            print(f"switch parse failed: {e}")

    def parse_our_switch(self, line: str):
        try:
            parts = line.split('|')
            if len(parts) >= 4:
                pokemon_ident = parts[2]  # "p1a: Wigglytuff"
                details = parts[3]        # "Wigglytuff, L95, M"
                condition = parts[4] if len(parts) > 4 else "100/100"

                pokemon_name = pokemon_ident.split(
                    ': ')[1] if ': ' in pokemon_ident else pokemon_ident.replace('p1a', '').strip()

                # update our trainer's active pokemon
                if self.battle_data.trainer:
                    for pokemon in self.battle_data.trainer.team:
                        if pokemon_name in pokemon.ident:
                            # set all pokemon inactive first
                            for p in self.battle_data.trainer.team:
                                p.active = False
                            # set this one active
                            pokemon.active = True
                            print(f"Switched to: {pokemon_name}")
                            break

        except Exception as e:
            print(f"our switch parse failed: {e}")

    def parse_opponent_move(self, line: str):
        try:
            parts = line.split('|')
            if len(parts) >= 3:
                pokemon_ident = parts[2]
                move_name = parts[3] if len(parts) > 3 else "Unknown"

                if pokemon_ident in self.opponent_team:
                    pokemon = self.opponent_team[pokemon_ident]
                    if move_name not in pokemon.moves_seen:
                        pokemon.moves_seen.append(move_name)
                        print(f"{pokemon.name} used: {move_name}")

        except Exception as e:
            print(f"move parse failed: {e}")

    def parse_opponent_hp_change(self, line: str):
        try:
            parts = line.split('|')
            if len(parts) >= 3:
                pokemon_ident = parts[2]
                new_condition = parts[3] if len(parts) > 3 else ""

                if pokemon_ident in self.opponent_team:
                    # check if fainted
                    if 'fnt' in new_condition:
                        pokemon = self.opponent_team[pokemon_ident]
                        pokemon.hp_percentage = 0
                        pokemon.active = False
                        print(f"{pokemon.name} fainted!")
                    else:
                        hp_info = self.parse_hp_condition(new_condition)
                        pokemon = self.opponent_team[pokemon_ident]
                        pokemon.hp_percentage = hp_info['hp_percentage']
                        pokemon.status = hp_info.get('status')
                        print(
                            f"{pokemon.name} HP: {hp_info['hp_percentage']}%")

        except Exception as e:
            print(f"hp parse failed: {e}")

    def parse_opponent_ability(self, line: str):
        try:
            parts = line.split('|')
            if len(parts) >= 4:
                pokemon_ident = parts[2]
                ability = parts[3]

                if pokemon_ident in self.opponent_team:
                    self.opponent_team[pokemon_ident].ability = ability
                    print(
                        f"{self.opponent_team[pokemon_ident].name} ability: {ability}")

        except Exception as e:
            print(f"ability parse failed: {e}")

    def parse_opponent_item(self, line: str):
        try:
            parts = line.split('|')
            if len(parts) >= 4:
                pokemon_ident = parts[2]
                item = parts[3]

                if pokemon_ident in self.opponent_team:
                    self.opponent_team[pokemon_ident].item = item
                    print(
                        f"{self.opponent_team[pokemon_ident].name} item: {item}")

        except Exception as e:
            print(f"item parse failed: {e}")

    def parse_opponent_status(self, line: str):
        try:
            parts = line.split('|')
            if len(parts) >= 4:
                pokemon_ident = parts[2]
                status = parts[3]

                if pokemon_ident in self.opponent_team:
                    self.opponent_team[pokemon_ident].status = status
                    print(
                        f"{self.opponent_team[pokemon_ident].name} status: {status}")

        except Exception as e:
            print(f"status parse failed: {e}")

    def get_opponent_summary(self) -> Dict:
        summary = {
            'active_pokemon': None,
            'team': [],
            'total_seen': len(self.opponent_team)
        }

        for ident, pokemon in self.opponent_team.items():
            pokemon_info = {
                'name': pokemon.name,
                'species': pokemon.species,
                'level': pokemon.level,
                'gender': pokemon.gender,
                'hp_percentage': pokemon.hp_percentage,
                'status': pokemon.status,
                'active': pokemon.active,
                'moves_seen': pokemon.moves_seen,
                'ability': pokemon.ability,
                'item': pokemon.item
            }

            summary['team'].append(pokemon_info)

            if pokemon.active:
                summary['active_pokemon'] = pokemon_info

        return summary

    async def battle_loop(self, websocket, message, state: SharedState):
        turn_stats = str(message).split("\n")
        self.battle_data.battle_id = turn_stats[0][1:] if turn_stats[0].startswith(
            '>') else ""

        # always process the log
        self.process_battle_log(turn_stats)

        if "|request|" in str(message):
            try:
                print("Received request, making Trainer")
                # find the request line
                request_line = None
                for line in turn_stats:
                    if line.startswith("|request|"):
                        request_line = line
                        break

                if request_line:
                    pokemon_stats = request_line.replace("|request|", "")
                    player_dict = json.loads(pokemon_stats)

                    if "active" in player_dict:
                        team = self.parse_pokemon(player_dict)
                        self.battle_data.trainer = Trainer(
                            name=player_dict["side"]["name"],
                            id=player_dict["side"]["id"],
                            team=team,
                            active_moves=player_dict["active"][0]["moves"],
                        )

                    elif "forceSwitch" in player_dict:
                        id = self.battle_data.trainer.get_next_available()
                        if id:
                            payload = f"{self.battle_data.battle_id}|/choose switch {id}"
                            await websocket.send(payload)

            except JSONDecodeError as e:
                print(f"json failed: {e}")
                pass
            except Exception as e:
                print(f"request failed: {e}")

        # run agents if we can
        if ("|request|" in str(message) or "|turn|" in str(message)) and self.battle_data.trainer:
            print("RUNNING AGENTS")

            # debug opponent info
            opponent_summary = self.get_opponent_summary()
            if opponent_summary['active_pokemon']:
                active = opponent_summary['active_pokemon']
                print(
                    f"vs {active['name']} Lv.{active['level']} HP:{active['hp_percentage']}%")
                if active['moves_seen']:
                    print(f"moves: {', '.join(active['moves_seen'])}")
                if active['ability']:
                    print(f"ability: {active['ability']}")
                if active['item']:
                    print(f"item: {active['item']}")
            print(f"seen {opponent_summary['total_seen']} pokemon")

            analysis_agent = AnalysisAgent(self.battle_data)
            decision_agent = DecisionAgent(self.battle_data)
            history_agent = HistoryAgent(self.battle_data)
            battle_agent = BattleAgent(self.battle_data)

            state = analysis_agent.execute_agent(state)
            state = decision_agent.execute_agent(state)
            battle_agent.execute_agent(state)
            hist = history_agent.execute_agent(message)

            history_arr = state["history"]
            history_arr.append(hist["summary"])
            state["history"] = history_arr

            if self.battle_data.move_queue:
                await websocket.send(self.battle_data.move_queue.pop())

    async def authenticate(self, websocket, message):
        data = get_challenge_data(message[10:], self.username, self.password)
        assert_str = f"|/trn {self.username},0,{data['assertion']}"
        await websocket.send(assert_str)
        await asyncio.sleep(5)

    def parse_pokemon(self, player_dict: Dict) -> List[Pokemon]:
        pokemon_data = player_dict["side"]["pokemon"]
        team = []
        for pokemon_dict in pokemon_data:
            team.append(
                Pokemon(
                    ident=pokemon_dict["ident"],
                    details=pokemon_dict["details"],
                    condition=pokemon_dict["condition"],
                    active=pokemon_dict["active"],
                    stats=pokemon_dict["stats"],
                    moves=pokemon_dict["moves"],
                    item=pokemon_dict["item"],
                    ability=pokemon_dict["ability"],
                )
            )
        return team
