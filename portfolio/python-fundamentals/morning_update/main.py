from openai_client import generate_text


if __name__ == "__main__":
    update = generate_text("Give me a short morning update about global stock markets.")
    print(update) 
