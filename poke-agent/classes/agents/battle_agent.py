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
from utils.helpers import print_agent_function_call

class BattleAgent:
    def __init__(self, battle_data: BattleData):

        self.toolkit = AgentToolkit(battle_data)
        self.battle_data = battle_data
        self.llm = genai.GenerativeModel(
            model_name="gemini-2.0-flash-lite",
            # model_name="gemini-1.5-pro",
            tools=[
                self.choose_move,
                self.swap_pokemon,
            ],
            generation_config={"temperature": 0},
            safety_settings=safety_filters,
        )


        self.graph = StateGraph(SharedState)  # Create a new graph

        self.graph.add_node("select_move", self.select_move)

        # Define entry point and edges
        self.graph.set_entry_point("select_move")

        # Compile the graph
        self.executor = self.graph.compile()

    def select_move(self, state: SharedState):
        
        chat = self.llm.start_chat(enable_automatic_function_calling=True)
        
        msg = f"""
            
            You are in a team of professional pokemon players. You are in a competitive battle in Pokemon Showdown.
            In your team, you have a researcher and a captain. The researcher and captain have deliberated.
            The Captain will now give you his thought process and decision. 
            Your job is to execute their plan.

            Address your team in the response.
            
            Captains deliberation: '{state["decision"]}'
        """

        response = None
        while response is None:
            try:
                response = chat.send_message(msg).text
                print(response)
            except ResourceExhausted:
                print("[bold purple]Sleeping...[/bold purple]")
                time.sleep(15)
        print(
            f"[bold bright_red]Battle Agent\n{response}[/bold bright_red]"
        )
        
        return state

    # Tool
    def choose_move(self, move_name: str):
        """Trigger the next move to be used"""
        print_agent_function_call("choose_move", move_name)
        move_id = 0
        moves = self.battle_data.trainer.active_moves
        for i, move in enumerate(moves):
            if move_name == move["move"]:
                move_id = i

        payload = f"{self.battle_data.battle_id}|/choose move {move_id+1}"
        print("p:", payload)
        self.battle_data.move_queue.append(payload)

    def swap_pokemon(self, pokemon_name: str):
        """Swap your current pokemon for a pokemon in your team"""
        print_agent_function_call("swap_pokemon", pokemon_name)
        pokemon_id = self.battle_data.trainer.get_pokemon_id(pokemon_name=pokemon_name)
        payload = f"{self.battle_data.battle_id}|/choose switch {pokemon_id}"
        print("p:", payload)
        self.battle_data.move_queue.append(payload)


    def execute_agent(self, state: SharedState):
        return self.executor.invoke(state)

