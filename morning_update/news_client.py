# In this task we'll use the newsapi.org API to fetch the most recent news headlines.
# We plan to include these headlines in the OpenAI prompt later, so we'll need the title and a short description for each of the items.

import requests
from config import API_KEY_NEWSAPI

NEWSAPI_TOP_HEADLINES_URL = "https://newsapi.org/v2/top-headlines"



def get_news_headlines () :
    headline_articles = []
    newsapi_url_params = {"country" : "sa",
                        "pageSize" : 5,
                        }
    newsapi_headers = {
        "Authorization": f" bearer {API_KEY_NEWSAPI}",
        "Content-Type": "application/json"
    }
    
    try: 
        response = requests.get(NEWSAPI_TOP_HEADLINES_URL, newsapi_url_params, newsapi_headers, timeout=30)
        response.raise_for_status() #raises HTTPError for bad status codes
        #return response
    except requests.exceptions.ConnectionError:
        print("Network connection failed")
        return None
    except requests.exceptions.Timeout:
        print("Request timed out")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error {e.response.status_code}: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

    #another way to implement bad status code 
    #    if response.status_code != 200:
    #       sys.exit(f"Error: Unexpected status code {response.status_code}")
    
    #now let's retrieve list of articles with only title and description
    for article in response.articles :
        headline_articles.append({"title":article.tilte, "description":article.description})

    return headline_articles
