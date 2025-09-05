from openai_client import generate_text
from news_client import get_news_headlines
from meteo_client import get_weather_forecast


def check_data_availability(weather_data, headlines_data):
    """Validate if we have the required data to generate the update"""
    if not weather_data:
        raise ValueError("No weather data available. Please check the city name or API connection.")
    
    if not headlines_data:
        raise ValueError("No news headlines available. Please check your news API connection.")
    
    return True


if __name__ == "__main__":
    try:
        # Get weather data
        weather = get_weather_forecast("dakar, Senegal")  # Change to your preferred city
          
        # Get news headlines
        NUM_HEADLINES = 3
        SOURCE_COUNTRY_CODE = "us"  # Change to your preferred country code
        headlines_list = get_news_headlines(SOURCE_COUNTRY_CODE) 
        headlines_list = headlines_list[:NUM_HEADLINES]
        
        # Validate data before proceeding
        check_data_availability(weather, headlines_list)
        
        # Prepare the update message
        user_message = f'''Please generate a 'Morning Update' text in a funny and light tone.
Here is the Weather Forecast for the city of {weather["name"]}: 
{weather}
Here are the News Headlines in JSON format:
{headlines_list}
Generate the text as specified in the system prompt, following the structure of greeting, weather summary, {NUM_HEADLINES} headlines, and a closing remark.
        '''
        
        # Generate and display the update
        update_message = generate_text(user_message)
        print(update_message)
        
    except ValueError as ve:
        print(f"Error: {str(ve)}")
        exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        print("Please check your API connections and try again.")
        exit(1)
