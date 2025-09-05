from openai_client import generate_text
from news_client import get_news_headlines
from meteo_client import get_weather_forecast


if __name__ == "__main__":
    
    #testing open ai api call to generate a text from a prompt
    #update = generate_text("Give me a short morning update about global stock markets.")
    #print(update) 

    #testing news api 
    NUM_HEADLINES = 10  # Configurable number of headlines
    headlines_list = get_news_headlines()[:NUM_HEADLINES]
    #print(headlines_list)

    #testing meteo api call
    weather = get_weather_forecast("mississauga")
    #print(weather)


    #Generating the update message with open ai api call to generate a text from a prompt

    user_message = f'''Please generate a 'Morning Update' text in a funny and light tone.
Here is the Weather Forecast: 
{weather}
Here are the News Headlines in JSON format:
{headlines_list}
Generate the text as specified in the system prompt, following the structure of greeting, weather summary, 10 headlines, and a closing remark.
    '''
    print(user_message)
    
    update_message = generate_text(user_message)
    print(update_message)
    #print(update) 
