# In this task we'll use the newsapi.org API to fetch the most recent news headlines.
# API docs https://newsapi.org/docs/endpoints/top-headlines
# We plan to include these headlines in the OpenAI prompt later, so we'll need the title and a short description for each of the items.

import requests
from config import API_KEY_NEWSAPI

NEWSAPI_TOP_HEADLINES_URL = "https://newsapi.org/v2/top-headlines"



def get_news_headlines () :
    headline_articles = []
    newsapi_url_params = {"country" : "ca",
                        #"pageSize" : 5,
                        }
    newsapi_headers = {
        #"Authorization": f"Bearer {API_KEY_NEWSAPI}",
        "X-Api-Key": API_KEY_NEWSAPI        
    }
    
    try: 
        response = requests.get(NEWSAPI_TOP_HEADLINES_URL, params=newsapi_url_params, headers=newsapi_headers, timeout=30)
        response.raise_for_status() #raises HTTPError for bad status codes
        data = response.json()
        #return response
        
        #print(response.status_code) #debugging line to see the status code
        #print(response.json())  #debugging line to see the full response
        print("news"+"*" * 20)
        print(data.keys())  #debugging line to see the keys in the response
        print("*" * 20)
        print(data["articles"][0])  #debugging line to see the first article in the response
        print("*" * 20)
        print(len(data["articles"]))  #debugging line to see how many articles were returned
        
        #now let's retrieve list of articles with only title and description
        for article in data["articles"]: 
            headline_articles.append({
                "title": article.get("title","No Title"), #use get method to avoid KeyError if key is missing
                "description":article.get("description","No Description")
                })

        return headline_articles 


    except requests.exceptions.ConnectionError:
        print("Network connection failed")
    except requests.exceptions.Timeout:
        print("Request timed out")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error {e.response.status_code}: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    return []

    #another way to implement bad status code 
    #    if response.status_code != 200:
    #       sys.exit(f"Error: Unexpected status code {response.status_code}")
    


    
