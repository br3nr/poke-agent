import requests

class DexAPIClient:

    def __init__(self, base_url="http://localhost:3000"):
        self.base_url = base_url
        self.session = requests.Session()

    def get_pokemon(self, pokemon: str):
        url = f"{self.base_url}/pokemon?pokemon={pokemon}"
        print(f"[bold purple]Sending request: {url}[/bold purple]")
        response = self.session.get(url)
        return response.json()

    def get_move(self, move: str):
        url = f"{self.base_url}/move?move={move}"
        print(f"[bold purple]Sending request: {url}[/bold purple]")
        response = self.session.get(url)
        return response.json()

    def get_ability(self, ability: str):
        url = f"{self.base_url}/ability?ability={ability}"
        print(f"[bold purple]Sending request: {url}[/bold purple]")
        response = self.session.get(url)
        return response.json()
