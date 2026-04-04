import requests
from classes.models import PokemonData, MoveData, AbilityData
from pprint import pprint as print

class DexAPIClient:
    def __init__(self, base_url="http://localhost:3000", debug=False):
        self.base_url = base_url
        self.session = requests.Session()
        self.debug = debug

    def _debug_print(self, message: str):
        if self.debug:
            print(message)

    def _log_request(self, url: str):
        if self.debug:
            print(f"[bold purple]Sending request: {url}[/bold purple]")

    def get_pokemon(self, pokemon: str) -> PokemonData:
        self._debug_print(f"[debug] Looking up pokemon: '{pokemon}'")
        url = f"{self.base_url}/pokemon?pokemon={pokemon}"
        self._log_request(url)
        response = self.session.get(url)
        pokemon_data = response.json()
        return PokemonData(**pokemon_data)

    def get_move(self, move: str) -> MoveData:
        url = f"{self.base_url}/move?move={move}"
        self._log_request(url)
        response = self.session.get(url)
        move_data = response.json()
        return MoveData(**move_data)

    def get_ability(self, ability: str) -> AbilityData:
        url = f"{self.base_url}/ability?ability={ability}"
        self._log_request(url)
        response = self.session.get(url)
        ability_data = response.json()
        return AbilityData(**ability_data)

    def get_filtered_move(self, move: str) -> MoveData | None:
        self._debug_print(f"[debug] Filtering move: '{move}'")

        # TODO: Check if fmt is still needed
        move_name_fmt = move.lower().replace(" ", "-")

        if "hidden-power" in move_name_fmt:
            # TODO: Determine better way to handle edge cases
            move_name_fmt = "hidden-power"
            self._debug_print(f"[debug] Converted to hidden-power format")
        elif "return-102" in move_name_fmt:
            # because it does up to 102, always in showdown 102
            move_name_fmt = "return"
            self._debug_print(f"[debug] Converted return-102 to return")

        self._debug_print(f"[debug] Final move name: '{move_name_fmt}'")
        return self.get_move(move_name_fmt)
