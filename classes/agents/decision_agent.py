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
            model_name='gemini-2.5-pro-exp-03-25',
            safety_settings=safety_filters,
        )

        chat = model.start_chat()

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

'''
class AnalysisAgent:
    def __init__(self):
        self.toolkit = AgentToolkit()
        self.battle_data = BattleData()

        self.llm = genai.GenerativeModel(
            model_name="gemini-1.5-flash-001",
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

        self.graph = StateGraph(AnalysisState)  # Create a new graph

        self.graph.add_node("analysis", self.analysis)

        # Define entry point and edges
        self.graph.set_entry_point("analysis")

        # Compile the graph
        self.executor = self.graph.compile()

    def analysis(self, state: AnalysisState):

        #user_input = state["input"]
        #response = self.llm.invoke(user_input)
        chat = self.llm.start_chat(enable_automatic_function_calling=True)

        msg = f""" 
        You are in a team of professional pokemon players. Together you are united in a competitive battle in Pokemon Showdown.
        You have been given the researcher tole in the team. Your job, is to collect the facts that are available to you through your available functions.
        
        Your current pokemon is {self.battle_data.trainer.get_active_pokemon().name}
        You are currently facing off against a {self.battle_data.opponent.active_pokemon}.

        Your task is simple, but vital. Put together the facts you have obtained about the current state of the battle, and output it in a concise format. 
        
        Your team need to know the following: 
            - Details about the current pokemon. What their moves are, the damage class (status or attack), damage type, etc.
            - What their resistances / weaknesses are. 
            - Who you have available on your team, their moves and resistances / weaknesss. 
            - The opponent, their moves, what their type is, weakness etc.

        It is important that you are as detailed as you can be about each of these.
        
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
            f"[bold bright_yellow]Analysis Agent\n{response}[/bold bright_yellow]"
        )
         
        state["response"] = response
        return state 


    def execute_agent(self):
      return self.executor.invoke({"query":"hello"})["response"]
  '''
