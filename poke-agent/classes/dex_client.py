import requests
from classes.models import PokemonData, MoveData, AbilityData

class DexAPIClient:

    def __init__(self, base_url="http://localhost:3000"):
        self.base_url = base_url
        self.session = requests.Session()

    def get_pokemon(self, pokemon: str) -> PokemonData:
        print(f"[debug] Looking up pokemon: '{pokemon}'")
        url = f"{self.base_url}/pokemon?pokemon={pokemon}"
        print(f"[bold purple]Sending request: {url}[/bold purple]")
        response = self.session.get(url)
        pokemon_data = response.json()
        return PokemonData(**pokemon_data)
    
    def get_move(self, move: str) -> MoveData:
        url = f"{self.base_url}/move?move={move}"
        print(f"[bold purple]Sending request: {url}[/bold purple]")
        response = self.session.get(url)
        move_data = response.json()
        return MoveData(**move_data)
    

    def get_ability(self, ability: str) -> AbilityData:
        url = f"{self.base_url}/ability?ability={ability}"
        print(f"[bold purple]Sending request: {url}[/bold purple]")
        response = self.session.get(url)
        ability_data = response.json()
        return AbilityData(**ability_data)

    def get_filtered_move(self, move: str) -> MoveData | None:
        # TODO: Check if fmt is still needed
        move_name_fmt = move.lower().replace(" ", "-")
        if "hidden-power" in move_name_fmt:
            # TODO: Determine better way to handle edge cases
            move_name_fmt = "hidden-power"
        elif "return-102" in move_name_fmt:
            # because it does up to 102, always in showdown 102
            move_name_fmt = "return"
        
        return self.get_move(move_name_fmt)