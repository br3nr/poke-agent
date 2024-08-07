import requests

class SmogonClient:
    BASE_URL = "https://www.smogon.com/dex/_rpc/"

    @staticmethod
    def get_basics(gen: str) -> dict:
        url = f"{SmogonClient.BASE_URL}dump-basics"
        payload = {"gen": gen}
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def get_pokemon(gen: str, pokemon: str) -> dict:
        url = f"{SmogonClient.BASE_URL}dump-pokemon"
        payload = {"gen": gen, "alias": pokemon, "language": "en"}
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def get_format(gen: str, format: str) -> dict:
        url = f"{SmogonClient.BASE_URL}dump-format"
        payload = {"gen": gen, "alias": format, "language": "en"}
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
