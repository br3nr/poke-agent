
from utils.config import safety_filters
import google.generativeai as genai
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
from classes.battle_data import BattleData
from rich import print 
from utils.helpers import (
    get_challenge_data,
    get_types,
    get_pokemon_info,
    get_damage_relations,
    print_agent_function_call,
)

class BattleAgent:

    def __init__(self):
        self.battle_data = BattleData()

    def execute_agent(self, decision):
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash-001",
            # model_name="gemini-1.5-pro",
            tools=[
                self.choose_move,
                self.swap_pokemon,
            ],
            generation_config={"temperature": 0},
            safety_settings=safety_filters,
        )

        chat = model.start_chat(enable_automatic_function_calling=True)

        msg = f"""
            
            You are in a team of professional pokemon players. You are in a competitive battle in Pokemon Showdown.
            In your team, you have a researcher and a captain. The researcher and captain have deliberated.
            The Captain will now give you his thought process and decision. 
            Your job is to execute their plan.

            Captains deliberation: '{decision}'
        """

        response = None
        while response is None:
            try:
                response = chat.send_message(msg).text
            except ResourceExhausted:
                print("[bold purple]Sleeping...[/bold purple]")
                time.sleep(15)

        print(
            f"[bold bright_red]Orchestrator Agent\n{response}[/bold bright_red]"
        )

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

