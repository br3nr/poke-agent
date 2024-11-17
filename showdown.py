import asyncio
import os
import json
import google.generativeai as genai

from classes.client import ShowdownClient

from dotenv import load_dotenv
load_dotenv()

USERNAME = os.environ.get("SHOWDOWN_USERNAME")
PASSWORD = os.environ.get("SHOWDOWN_PASSWORD")
OPPONENT = "br3nr"

client = ShowdownClient(username=USERNAME, password=PASSWORD, opponent_name=OPPONENT)
api_key = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

asyncio.run(client.showdown_client())

