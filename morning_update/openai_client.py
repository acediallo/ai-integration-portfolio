# openai_client.py
from openai import OpenAI
from config import API_KEY_OPENAI

# Initialize OpenAI client
client = OpenAI(api_key=API_KEY_OPENAI)

def generate_text(prompt: str) -> str:
    """
    Generates text using OpenAI GPT model.
    """
    system_message = '''You are an AI assistant tasked with generating a 'Morning Update' text that’s engaging and enjoyable for the user to listen to while having their morning coffee. The update should be about 2-5 minutes long, incorporating both a weather forecast and top 10 news headlines in a way that feels conversational, lively, and fits a specific tone (such as funny, serious, sarcastic, or motivational). Do not output anything else than the text, don't include any markup, lists, or other structural elements. The text will be sent to a text-to-speech API to generate an MP3, so make sure the output contains nothing that should not be read out loud.

Structure the monologue as follows:

1. Greeting: Start with a warm and welcoming greeting.
2. Weather Summary: Describe the day’s weather, infusing the chosen tone (e.g., funny, serious, etc.) to make it engaging.
3. News Headlines: Present each headline in the chosen tone, followed by a summary of the headline to give the listener a deeper insight into the headline.
4. Closing: Wrap up with a concluding remark that leaves the reader with a smile, positive thought, or playful nudge.

Be creative in how you incorporate the tone and style, ensuring that the text is engaging and enjoyable to listen to.
'''

    response = client.chat.completions.create(
        model="gpt-4o-mini",  # lighter, cheaper model (good for summaries/updates)
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content
