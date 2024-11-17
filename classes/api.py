import requests
from typing import List, Dict, Optional

class DexAPI:
    BASE_URL = "https://www.smogon.com/dex/_rpc/"
    
    def __init__(self, gen: str = "sv") -> None:
        self.gen = gen
        self.all_data = self.get_all_basics(gen=gen)

    @staticmethod
    def get_all_basics(gen: str) -> dict:
        url = f"{DexAPI.BASE_URL}dump-basics"
        payload = {"gen": gen}
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def get_all_pokemon(gen: str, pokemon: str) -> dict:
        url = f"{DexAPI.BASE_URL}dump-pokemon"
        payload = {"gen": gen, "alias": pokemon, "language": "en"}
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def get_all_format(gen: str, format: str) -> dict:
        url = f"{DexAPI.BASE_URL}dump-format"
        payload = {"gen": gen, "alias": format, "language": "en"}
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    def get_pokemon(self, name: str) -> dict:
        for pokemon in self.all_data["pokemon"]:
            if pokemon["name"].lower() == name.lower():
                return pokemon
        return {}

    def get_move(self, name: str) -> dict:
        for move in self.all_data["moves"]:
            if move["name"].lower().replace(" ", "").replace("-","") == name.lower().replace(" ", "").replace("-",""):
                return move
        return {}

    def get_type(self, name: str) -> dict:
        for type in self.all_data["types"]:
            if type["name"].lower() == name.lower():
                return type
        return {}