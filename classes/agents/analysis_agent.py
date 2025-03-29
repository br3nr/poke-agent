from utils.config import safety_filters
import google.generativeai as genai
import time
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
from classes.battle_data import BattleData
from rich import print
from classes.agent_toolkit import AgentToolkit

class AnalysisAgent:
    
    def __init__(self):
        self.toolkit = AgentToolkit()
        self.battle_data = BattleData()
    def execute_agent(self):
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash-001",
            # model_name="gemini-1.5-pro",
            tools=[
                self.toolkit.get_pokemon_details,
                self.toolkit.get_current_moves,
                self.toolkit.get_opponent_pokemon_details,
                self.toolkit.get_team_details,
                self.toolkit.check_type_advantages,
            ],
            generation_config={"temperature": 0},
            safety_settings=safety_filters,
        )

        chat = model.start_chat(enable_automatic_function_calling=True)

        msg = f""" 
        You are in a team of professional pokemon players. Together you are united in a competitive battle in Pokemon Showdown.
        You have been given the researcher tole in the team. Your job, is to collect the facts that are available to you through your available functions.
        
        Your current pokemon is {self.battle_data.trainer.get_active_pokemon().name}
        You are currently facing off against a {self.battle_data.opponent.active_pokemon}.

        Your task is simple, but vital. Put together the facts you have obtained about the current state of the battle, and output it in a concise format. 
        
        Your team need to know the following: 
            - Details about the
            - What their resistances / weaknesses are
            - Who you have available, their moves and resistances / weaknesses
            - Who else is in your team
        
        Do not make any interpretations about the data, or suggestions. You must purely reconsturct the data in a concise format. 
        """

        response = None
        while response is None:
            try:
                response = chat.send_message(msg).text
            except ResourceExhausted:
                print("[bold purple]Sleeping...[/bold purple]")
                time.sleep(15)

        print(
            f"[bold bright_yellow]Orchestrator Agent\n{response}[/bold bright_yellow]"
        )
        
        return response

