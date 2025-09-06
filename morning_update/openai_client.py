# openai_client.py

import logging
from pathlib import Path 
from datetime import datetime
from openai import OpenAI
from config import API_KEY_OPENAI

# Initialize OpenAI client
client = OpenAI(api_key=API_KEY_OPENAI)

# Function to generate the morning update text
def generate_update(weather, headlines: list ) -> str:
    """
    Generates text using OpenAI GPT model.
    """
    system_message = '''You are an AI assistant tasked with generating a 'Morning Update' text that’s engaging and enjoyable for the user to listen to while having their morning coffee. The update should be about 2-5 minutes long, incorporating both a weather forecast and top 10 news headlines in a way that feels conversational, lively, and fits a specific tone (such as funny, serious, sarcastic, or motivational). Do not output anything else than the text, don't include any markup, lists, or other structural elements. The text will be sent to a text-to-speech API to generate an MP3, so make sure the output contains nothing that should not be read out loud.

    Structure the monologue as follows:

    1. Greeting: Start with a warm and welcoming greeting.
    2. Weather Summary: Describe the day’s weather and name EXPLICITLY the city, infusing the chosen tone (e.g., funny, serious, etc.) to make it engaging.
    3. News Headlines: Present each headline in the chosen tone, followed by a summary of the headline to give the listener a deeper insight into the headline.
    4. Closing: Wrap up with a concluding remark that leaves the reader with a smile, positive thought, or playful nudge.

    Be creative in how you incorporate the tone and style, ensuring that the text is engaging and enjoyable to listen to.
    '''

    # Definning the prompt to generate the update
        # Prepare the update message
    user_message = f'''Please generate a 'Morning Update' text in a funny and light tone.
    Here is the Weather Forecast for the city of {weather["name"]}: 
    {weather}
    Here are the News Headlines in JSON format:
    {headlines}
    Generate the text as specified in the system prompt, following the structure of greeting,
    weather summary, headlines, and a closing remark.
    '''

    response = client.chat.completions.create(
        model="gpt-4o-mini",  # lighter, cheaper model (good for summaries/updates)
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ],
    )
    return response.choices[0].message.content



# Text-to-Speech (TTS) functionality  
logging.basicConfig(level=logging.INFO)
AUDIO_DIR = Path(__file__).parent / "output"
AUDIO_DIR.mkdir(exist_ok=True)


def text_to_speech(text: str, voice: str) -> Path:
    """
    Convert `text` to MP3. Uses streaming if available.
    Returns Path to the saved file.
    """
    # Build a timestamped filename
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = AUDIO_DIR / f"morning_update_{ts}.mp3"
    #out_path.parent.mkdir(parents=True, exist_ok=True) # ensure dir exists

    try:
        logging.info("Using non-streaming TTS API...")
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text,
            response_format="mp3"
        )
        with open(out_path, "wb") as f:
            f.write(response)
        logging.info("Saved (non-stream) %s", out_path)
        return out_path


        """ streaming_api = getattr(client.audio.speech, "with_streaming_response", None)
        if streaming_api is not None:
            logging.info("Using streaming TTS API...")
            with streaming_api.create(model="tts-1", voice=voice, input=text, response_format="mp3") as resp:
                # If SDK provides stream_to_file convenience:
                if hasattr(resp, "stream_to_file"):
                    resp.stream_to_file(out_path)
                else:
                    # Generic fallback: iterate bytes and write
                    with open(out_path, "wb") as f:
                        for chunk in resp.iter_bytes():
                            f.write(chunk)
            logging.info("Saved (stream) %s", out_path)
            return out_path
        else:
            logging.info("Using non-streaming TTS API...")
            response = client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text,
                response_format="mp3"
            )
            with open(out_path, "wb") as f:
                f.write(response)
            logging.info("Saved (non-stream) %s", out_path)
            return out_path """
    except Exception as e:
        logging.exception("TTS failed: %s", e)
        raise
