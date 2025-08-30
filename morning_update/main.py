#from openai_client import generate_text
from news_client import get_news_headlines


if __name__ == "__main__":
    
    #testing open ai api call to generate a text from a prompt
    #update = generate_text("Give me a short morning update about global stock markets.")
    #print(update) 

    #testing news api 
    headlines_list = get_news_headlines()[:5]  #get only first 5 headlines
    print(headlines_list)


