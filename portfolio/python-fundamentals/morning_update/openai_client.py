# openai_client.py
from openai import OpenAI
from config import API_KEY_OPENAI

# Initialize OpenAI client
client = OpenAI(api_key=API_KEY_OPENAI)

def generate_text(prompt: str) -> str:
    """
    Generates text using OpenAI GPT model.
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # lighter, cheaper model (good for summaries/updates)
        messages=[
            {"role": "system", "content": "You are a helpful assistant generating morning business updates."},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content
