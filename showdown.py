import asyncio
import os
import json

from classes.client import ShowdownClient

from dotenv import load_dotenv
load_dotenv()

USERNAME = os.environ.get("SHOWDOWN_USERNAME")
PASSWORD = os.environ.get("SHOWDOWN_PASSWORD")
OPPONENT = "br3nr"

client = ShowdownClient(username=USERNAME, password=PASSWORD, opponent=OPPONENT)

asyncio.run(client.showdown_client())

