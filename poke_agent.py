import pathlib
import textwrap
import time
import os 

import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()


genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))


model = genai.GenerativeModel(model_name='gemini-1.0-pro',
                              tools=[multiply])

chat = model.start_chat(enable_automatic_function_calling=True)




msg = "How are you today?"
response = chat.send_message(msg)

