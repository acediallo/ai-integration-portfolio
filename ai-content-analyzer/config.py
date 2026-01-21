# config.py
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

API_KEY_OPENAI = os.getenv("API_KEY_OPENAI")

if not API_KEY_OPENAI:
    raise ValueError("⚠️ API_KEY_OPENAI not set. Check your .env file.")
