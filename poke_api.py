import asyncio
import requests

def get_pokemon_info(name: str):
    resp = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name}")
    return resp.json()


def get_pokemon_type(name: str) -> str:
    resp_json = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name}").json()
    types = []
    for type_data in resp_json["types"]:
        types.append(type_data["type"]["name"])

    return str(types)
    
if __name__ == "__main__":
    print(get_pokemon_info("pikachu"))
    print(get_pokemon_type("charizard"))
