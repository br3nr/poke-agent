import os
import time
from dotenv import load_dotenv
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from rich import print
from google.api_core.exceptions import ResourceExhausted
import google.generativeai as genai

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, END

from utils.config import safety_filters
from classes.battle_data import BattleData
from classes.agent_toolkit import AgentToolkit
from classes.sharedstate import SharedState

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

        self.graph = StateGraph(SharedState)  # Create a new graph

        self.graph.add_node("get_analysis", self.get_analysis)

        # Define entry point and edges
        self.graph.set_entry_point("get_analysis")

        # Compile the graph
        self.executor = self.graph.compile()

    def get_analysis(self, state: SharedState):

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
         
        state["analysis"] = response
        return state 


    def execute_agent(self, state: SharedState):
        return self.executor.invoke(state)

