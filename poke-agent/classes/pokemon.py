from typing import List, Dict
import requests
from rich import print
from utils.helpers import get_types, get_move_details
from classes.dex_client import DexAPIClient
from classes.models import AbilityData, PokemonData, MoveData

class Pokemon:
    """
    "ident": "p1: Snorlax",
    "details": "Snorlax, L84, M",
    "condition": "406/406",
    "active": false,
    "stats": { "atk": 233, "def": 157, "spa": 157, "spd": 233, "spe": 99 },
    "moves": ["crunch", "curse", "return102", "earthquake"],
    "baseAbility": "thickfat",
    "item": "leftovers",
    "pokeball": "pokeball",
    "ability": "thickfat"
    """

    def __init__(
        self,
        ident: str,
        details: str,
        condition: str,
        active: bool,
        stats: Dict,
        moves: List[str],
        item: str,
        ability: str,
    ):
        self.ident = ident
        self.details = details
        self.condition = condition
        self.active = active
        self.stats = stats
        self.item = item
        self.ability = ability
        self.dex = DexAPIClient()

        move_list = []
        for move in moves:
            move_data = get_move_details(move)
            move_list.append({"name": move_data["name"], "type": move_data["type"]})    

        self.moves = move_list

        detail_arr = details.split(",")
        self.name = detail_arr[0].strip()
        self.types: List[str] = get_types(self.name)

    def get_ability_info(self):
        ability = self.dex.get_ability(ability=self.ability)
        return ability.shortDesc

    def get_pokemon_type(self, name: str) -> str:
        url = f"http://localhost:3000/pokemon?name={name}"
        print(f"[bold purple]Sending request: {url}[/bold purple]")
        resp_json = requests.get(url).json()
        types = resp_json["types"]
        return str(types)

    def __str__(self):
        formatted_moves = ", ".join(f"{move['name']} ({move['type']})" for move in self.moves)
        
        return (
            f"Name: {self.name}\n"
            f"ID: {self.ident}\n"
            f"Details: {self.details}\n"
            f"Condition: {self.condition}\n"
            f"Stats: {self.stats}\n"
            f"Moves: {formatted_moves}\n"
            f"Item: {self.item}\n"
            f"Ability: {self.ability}\n"
            f"Type: {', '.join(self.types)}"
        )
