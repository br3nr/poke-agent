import os
import time
from dotenv import load_dotenv
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from rich import print
from google.api_core.exceptions import ResourceExhausted
import google.generativeai as genai
from textwrap import dedent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, END

from utils.config import safety_filters
from classes.battle_data import BattleData
from classes.agent_toolkit import AgentToolkit
from classes.sharedstate import SharedState

class DecisionAgent:
    def __init__(self):

        self.toolkit = AgentToolkit()
        self.battle_data = BattleData()
        self.llm = genai.GenerativeModel(
            model_name='gemini-2.0-flash-thinking-exp-01-21',
            safety_settings=safety_filters,
        )

        self.graph = StateGraph(SharedState)  # Create a new graph

        self.graph.add_node("get_decision", self.get_decision)

        # Define entry point and edges
        self.graph.set_entry_point("get_decision")

        # Compile the graph
        self.executor = self.graph.compile()

    def get_decision(self, state: SharedState):

        chat = self.llm.start_chat()

        msg = dedent(f""" 
        You are in a team of professional pokemon players. Together you are united in a competitive battle in Pokemon Showdown.
        Your role in the team is Team Captain. You are the one who will make decisions based on the state of the game. 
        The Team Researcher has provided you with the following details about the state of the game: 
        
            Analysis Agent: '{state["analysis"]}' 

        We also have a history of the past few moves that you have made previosly:

            History: 
                '{state["history"][-5:]}'

        Given the above analysis, you must now make the call on what the best decision is.
        
        You have two options:
            1) Attack with one of the current moves
            2) Switch pokemon

        You should rely only on the information provided in the analysis. It is imperrative that you do not use pre-existing knowledge.
        For example, you should ONLY rely on the type details provided by the analysis agent. Do NOT assume any weaknesses or advantages.
        Take into account the previos moves you have made as well. These will be critical in your decision making.
        It is important that you factor in future play.
        Make sure you think through it carefully. 
        
        Address your team in the response.
        Once you have decided, concicely explain your logic. Give it in a bullet list. It must not be verbose. 
        As in, maximum 10 bullet points.
        Once you have explained, instruct the Team Battler on what they should do.
        """)

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
        
        state["decision"] = response

        return state

    def execute_agent(self, state: SharedState):
        return self.executor.invoke(state)

