from utils.config import safety_filters
import google.generativeai as genai
import time
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
from classes.battle_data import BattleData
from rich import print
from classes.agent_toolkit import AgentToolkit

class DecisionAgent:
    
    def __init__(self):
        self.toolkit = AgentToolkit()
        self.battle_data = BattleData()

    def execute_agent(self, analysis: str):
        model = genai.GenerativeModel(
            model_name='gemini-2.0-flash-thinking-exp-01-21',
            safety_settings=safety_filters,
        )

        chat = model.start_chat(enable_automatic_function_calling=True)

        msg = f""" 
        You are in a team of professional pokemon players. Together you are united in a competitive battle in Pokemon Showdown.
        Your role in the team is Team Captain. You are the one who will make decisions based on the state of the game. 
        The Team Researcher has provided you with the following details about the state of the game: 
        
            Analysis Agent: '{analysis}' 
        
        Given the above analysis, you must now make the call on what the best decision is.
        
        You have two options:
            1) Attack with one of the current moves
            2) Switch pokemon

        You should rely only on the information provided in the analysis. It is imperrative that you do not use pre-existing knowledge.
        For example, you should ONLY rely on the type details provided by the analysis agent. Do NOT assume any weaknesses or advantages.
        It is important that you factor in future play.
        Make sure you think through it carefully. 
        
        Once you have decided, concicely explain your logic. Give it in a bullet list. It must not be verbose. 
        As in, maximum 10 bullet points.
        Once you have explained, instruct the Team Battler on what they should do.
        """

        response = None
        while response is None:
            try:
                response = chat.send_message(msg).text
            except ResourceExhausted:
                print("[bold purple]Sleeping...[/bold purple]")
                time.sleep(15)

        print(
            f"[bold magenta]Decision Agent\n{response}[/bold magenta]"
        )
        
        return response

