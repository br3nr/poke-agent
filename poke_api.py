import asyncio
import requests

def get_pokemon_info(name: str):
    resp = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name}")
    return resp.json()

if __name__ == "__main__":
    get_pokemon_info("pikachu")

