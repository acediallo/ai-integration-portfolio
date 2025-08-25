# config.py
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

API_KEY_OPENAI = os.getenv("API_KEY_OPENAI")
API_KEY_NEWSAPI = os.getenv("API_KEY_NEWSAPI")
API_KEY_METEOSOURCE = os.getenv("API_KEY_METEOSOURCE")

if not API_KEY_OPENAI:
    raise ValueError("⚠️ API_KEY_OPENAI not set. Check your .env file.")
if not API_KEY_NEWSAPI:
    raise ValueError("⚠️ API_KEY_NEWSAPI not set. Check your .env file.")
if not API_KEY_METEOSOURCE:
    raise ValueError("⚠️ API_KEY_METEOSOURCE not set. Check your .env file.")
