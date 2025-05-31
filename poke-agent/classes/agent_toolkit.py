
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
from classes.dex_client import DexAPIClient
from classes.models import AbilityData, PokemonData, MoveData

from utils.helpers import (
    get_challenge_data,
    get_types,
    get_pokemon_info,
    get_damage_relations,
    print_agent_function_call,
)

class AgentToolkit():
    
    def __init__(self, battle_data: BattleData):
        self.battle_data = battle_data
        self.dex = DexAPIClient()

    def get_pokemon_details(self, pokemon_name: str) -> str:
        """Gets the details about one of the pokemon in your team"""
        team = self.battle_data.trainer.get_team()
        for mon in team:
            # print(mon.name, pokemon_name)
            if mon.name == pokemon_name:
                print_agent_function_call("get_pokemon_details", pokemon_name, mon)
                return str(mon)
        return "Could not find pokemon"

    def get_opponent_pokemon_details(self, pokemon_name: str) -> str:
        """Gets the details about the opponents pokemon"""
        types = get_types(pokemon_name)
        details = f"The opponets {pokemon_name} is a {' and '.join(types)} type pokemon."
        details += f"\n{self.check_type_advantages(pokemon_name)}"
        print_agent_function_call("get_opponent_pokemon_details", pokemon_name, details)
        
        return details


    def get_team_details(self, team_name: str = "team") -> str:
        """Returns all of the pokemon in the team"""
        team = self.battle_data.trainer.get_team()
        team_list = []
        for mon in team:
            if mon.condition != "0 fnt" or mon.name != self.battle_data.trainer.get_active_pokemon().name:
                team_list.append({"name": mon.name, "type": mon.types})
       
        print(str(team_list))
        print_agent_function_call("get_team_details", team_name, team_list)
        return str(team_list)

    def check_type_advantages(self, pokemon_name: str) -> str:
        """Takes the name of a pokemon. Returns the what types the pokemon is good and bad against."""
        types = get_types(pokemon_name=pokemon_name)
        relations = get_damage_relations(types)
        response = f"Here are the resistances, weaknesses and immunities for {pokemon_name}.\nNOTE: Asterisk * represents double factor on the weakness or resistance.\n{relations}"
        print_agent_function_call("check_type_advantages", pokemon_name, relations)
        return relations

    def get_current_moves(self):
        """Gets the available moves for your active Pokémon."""
        moves = self.battle_data.trainer.active_moves
        detailed_moves = []

        for move in moves:
            if move.get("disabled"):
                continue  # skip disabled moves

            move_name = move["move"]
            move_data = self.dex.get_filtered_move(move_name)

            if not move_data:
                continue

            detailed_moves.append({
                "name": move_name,
                "type": move_data.type,
                "class": move_data.category,       
                "accuracy": move_data.accuracy,
                "power": move_data.basePower,
                "description": move_data.shortDesc,
                "pp": move_data.priority,
            })

        return detailed_moves