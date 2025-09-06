
import requests
from config import API_KEY_METEOSOURCE


METEOSOURCE_API_URL = "https://www.meteosource.com/api/v1/free/point"

def get_weather_forecast(city: str):

    try:
        # First, get the place ID for the city
        get_place_id = requests.get("https://www.meteosource.com/api/v1/free/find_places_prefix", params={"text": city}, headers={"X-Api-Key": API_KEY_METEOSOURCE}, timeout=30)
        get_place_id.raise_for_status()
        place_data = get_place_id.json() 
        if not place_data:
            print(f"No place found for city: {city}")
            return {}
        
        # Assuming the first result is the desired city
        place_id = place_data[0]["place_id"]
        print(f"Place ID for {city}: {place_id}")  # Debugging line to check the place ID
        meteo_params = {
        "place_id": place_id,
        "language": "en",
        "units": "metric",
        #"sections" : "current"
        }

        # Now, get the weather data for the place ID
        response = requests.get(METEOSOURCE_API_URL, params=meteo_params,headers={"X-Api-Key": API_KEY_METEOSOURCE}, timeout=30)
        response.raise_for_status()  # Raises HTTPError for bad status codes
        data = response.json()
        
        # Debugging lines to inspect the response
        print("meteo"+"*" * 20)
        print(data.keys())  # Print the keys in the response
        #print("*" * 20)
        #print(data)  # Print the full response
        print("*" * 20)
        
        # Extract relevant weather information
        current_weather = data.get("current", {})
        summary = current_weather.get("summary", "No summary available")    
        temperature = current_weather.get("temperature")
        precipitation = current_weather.get("precipitation")

        precipitation_total = None
        precipitation_type = None
        if precipitation:
            precipitation_total = precipitation.get("total", None)
            precipitation_type = precipitation.get("TYPE", None)
        
        return {
            "name": place_data[0]["name"],
            "summary": summary,
            "temperature": temperature,
            "precipitation_total": precipitation_total,
            "precipitation_type": precipitation_type
        }
    
    except requests.exceptions.ConnectionError:
        print("Network connection failed")
    except requests.exceptions.Timeout:
        print("Request timed out")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error {e.response.status_code}: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    
    return {}
