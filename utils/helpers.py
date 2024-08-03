import requests
import json

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

