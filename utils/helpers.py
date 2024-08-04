import requests
import json
from rich import print
import re 
from typing import List, Dict
from requests.exceptions import JSONDecodeError
def get_challenge_data(challstr, username, password):
    payload = {
        "name": username,
        "pass": password,
        "challstr": challstr,
    }
    headers = {"User-Agent": "PokeAgentv1"}
    uri = "https://play.pokemonshowdown.com/api/login"
    response = requests.post(uri, data=payload, headers=headers)
    json_str = response.content.decode("utf-8")
    data = json.loads(json_str[1:])
    return data

def get_types(pokemon_name, ident=None):
    try:
        pokemon_data = get_pokemon_info(pokemon_name)
    except JSONDecodeError as e:
        if ident:
            print("[red]Retrying with ident[/red]")
            pokemon_data = get_pokemon_info(ident)

    types = []
    for t in pokemon_data["types"]:
        types.append(t["type"]["name"])
        get_damage_relations(t["type"]["name"])
    return types

def fix_name_format(name: str):
    name = re.sub(r'[^A-Za-z0-9\s-]', '',  name)
    match = re.match(r'^([^-]+-[^-]+)(-.*)?$', name)
    return match.group(1) if match else name

def get_pokemon_info(name: str):
    fixed_name = fix_name_format(name).replace(" ", "-")
    url = f"https://pokeapi.co/api/v2/pokemon/{fixed_name.lower()}"
    print(f"[bold purple]Sending request: {url}[/bold purple]")
    resp = requests.get(url)
    return resp.json()

def get_damage_relations(attack_type: str):
    url = f"https://pokeapi.co/api/v2/type/{attack_type}"
    print(f"[bold purple]Sending request: {url}[/bold purple]")
    data = requests.get(url).json()
    damage_relations = data["damage_relations"]

    super_effective_against = iterate_damage_relation(damage_relations, "double_damage_to")
    vulnerable_to = iterate_damage_relation(damage_relations, "double_damage_from")
    resistant_against = iterate_damage_relation(damage_relations, "half_damage_from")
    not_very_effective_against = iterate_damage_relation(damage_relations, "half_damage_to")
    immune_to = iterate_damage_relation(damage_relations, "no_damage_to")
    immune_from = iterate_damage_relation(damage_relations, "no_damage_from")

    return (
        f"Type: {attack_type.capitalize()}\n\n"
        f"Super effective against: {', '.join(super_effective_against)}\n"
        #f"Vulnerable to: {', '.join(vulnerable_to)}\n"
        #f"Resistant against: {', '.join(resistant_against)}\n"
        f"Not very effective against: {', '.join(not_very_effective_against)}\n"
        #f"Immune to: {', '.join(immune_to)}\n"
        #f"Immune from: {', '.join(immune_from)}\n"
    )

def iterate_damage_relation(data: List[Dict], category: str):
    damage_relations = []
    for damage_type in data[category]:
        damage_relations.append(damage_type["name"])
    return damage_relations