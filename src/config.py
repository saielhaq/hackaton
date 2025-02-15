from dotenv import load_dotenv
import os
load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")

def get_api_key():
    return API_KEY 