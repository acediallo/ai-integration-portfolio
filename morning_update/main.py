from openai_client import generate_update
from openai_client import text_to_speech
from news_client import get_news_headlines
from weather_client import get_weather_forecast


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
          
        # Get news headlines list
        
        headlines_list = get_news_headlines() 
        print(headlines_list)  # Debugging line to check the headlines list
        
        # Validate data before proceeding
        check_data_availability(weather, headlines_list)
                
        # Generate and display the update
        update_content = generate_update(weather, headlines_list)
        update_message = update_content["text"]
        print(f"Following is the generated update which costs ${update_content['cost']}: {update_message}")

        # Convert the update text to speech and save as MP3
        mp3_path = text_to_speech(update_message, voice="fable")
        print(f"Morning update saved to: {mp3_path}")
        
    except ValueError as ve:
        print(f"Error: {str(ve)}")
        exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        print("Please check your API connections and try again.")
        exit(1)
