import asyncio
import websockets
import requests
import json
import time
import json
import google.generativeai as genai
import re
import traceback
from google.api_core.exceptions import ResourceExhausted

from rich import print
from typing import List, Dict

from classes.trainer import Trainer
from classes.opponent import Opponent
from classes.agents.analysis_agent import AnalysisAgent
from classes.pokemon import Pokemon
from classes.api import DexAPI
from classes.battle_data import BattleData

from utils.config import safety_filters
from utils.helpers import (
    get_challenge_data,
    print_agent_function_call,
)

class ShowdownClient:

    def __init__(self, username, password, opponent_name):
        self.username = username
        self.password = password
        self.opponent_name = opponent_name
        self.websocket = None
        self.battle_data = BattleData()
        self.analysis_agent = AnalysisAgent()

    # Tool
    def choose_move(self, move_name: str):
        """Trigger the next move to be used"""
        print_agent_function_call("choose_move", move_name)
        move_id = 0
        moves = self.battle_data.trainer.active_moves
        for i, move in enumerate(moves):
            if move_name == move["move"]:
                move_id = i

        payload = f"{self.battle_data.battle_id}|/choose move {move_id+1}"
        print("p:", payload)
        self.battle_data.move_queue.append(payload)

    def swap_pokemon(self, pokemon_name: str):
        """Swap your current pokemon for a pokemon in your team"""
        print_agent_function_call("swap_pokemon", pokemon_name)
        pokemon_id = self.battle_data.trainer.get_pokemon_id(pokemon_name=pokemon_name)
        payload = f"{self.battle_data.battle_id}|/choose switch {pokemon_id}"
        print("p:", payload)
        self.battle_data.move_queue.append(payload)

    def process_battle_log(self, turn_stats):
        for turn in turn_stats:
            if "|switch|p2a:" in turn:
                match = re.search(r"\bp2a: (\w+)", turn)
                if match:
                    pokemon_name = match.group(1)
                    self.battle_data.opponent.active_pokemon = pokemon_name

    async def battle_loop(self, websocket, message):
        turn_stats = str(message).split("\n")
        self.battle_data.battle_id = turn_stats[0][1:]

        #        payload = f"{self.battle_data.battle_id}|/data gliscor"
        #        await self.websocket.send(payload)
        if "|request|" in str(message):  # and "active" in str(message):
            # get the player and team data
            try:
                pokemon_stats = turn_stats[1].replace("|request|", "")
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
            except Exception as e:
                traceback.print_exc()
                pass
        elif "|turn|" in turn_stats[len(turn_stats) - 1]:
            self.process_battle_log(turn_stats)
            self.main_agent_executor()
            await self.websocket.send(self.battle_data.move_queue.pop())

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

    async def showdown_client(self):
        # Must redefine User-Agent to prevent showdown auto-ban
        # as specified by showdown mods
        headers = {"User-Agent": "PokeAgentv1"}
        url = "wss://sim3.psim.us/showdown/websocket"

        self.websocket = await websockets.connect(url, extra_headers=headers)

        while True:
            # Wait for any incoming message or a timeout
            task = asyncio.wait_for(self.websocket.recv(), timeout=3000)
            message = await task
            if "challstr" in str(message):
                await self.authenticate(self.websocket, message)
                search_battle = f"|/challenge {self.opponent_name}, gen7randombattle"
                await self.websocket.send(search_battle)
            elif str(message).startswith(">battle"):
                await self.battle_loop(self.websocket, message)

    def main_agent_executor(self):

        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash-001",
            # model_name="gemini-1.5-pro",
            tools=[
                self.analysis_agent.get_agent_analyis,  # TODO: add back in next commit
                self.choose_move,
                self.swap_pokemon,
            ],
            generation_config={"temperature": 0},
            safety_settings=safety_filters,
        )

        chat = model.start_chat(enable_automatic_function_calling=True)

        msg = f"""
        
        You are an AI agent part of a larger agentic system. The system is responsible for taking actions in a pokemon battle. 
        Your task in the system is to orchestrate the other agents.
        Once your orchestration is complete, you will execute the next action.
        Your available actions are: 
            1) Change pokemon
            2) Execute move
        """

        response = None
        while response is None:
            try:
                response = chat.send_message(msg).text
            except ResourceExhausted:
                print("[bold purple]Sleeping...[/bold purple]")
                time.sleep(15)

        print(
            f"[bold bright_yellow]Orchestrator Agent\n{response}[/bold bright_yellow]"
        )
