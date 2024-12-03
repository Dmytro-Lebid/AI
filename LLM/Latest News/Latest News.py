# imports to retreive news articles
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

#imports to run application and AI API
import os
import json
from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr

# Initialization
load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')
if openai_api_key:
    print(f"OpenAI API Key exists and begins {openai_api_key[:8]}")
else:
    print("OpenAI API Key not set")
MODEL = "gpt-4o-mini"
openai = OpenAI()

system_message = "You are a helpful assistant who helps to find the latest news for a given topic."
system_message += "Always be accurate. If you don't know the answer, say so."

def get_latest_news_from_bing(topic):
    # Set up Selenium WebDriver
    options = Options()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Initialize the driver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # Search for the topic on Bing News
        search_url = f"https://www.bing.com/news/search?q={topic.replace(' ', '+')}"
        driver.get(search_url)

        # Wait for news results to load
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.news-card")))

        # Extract news articles
        articles = driver.find_elements(By.CSS_SELECTOR, "div.news-card")
        news_items = []

        for article in articles:
            try:
                # Extract the headline
                title_element = article.find_element(By.CSS_SELECTOR, "a.title")
                title = title_element.text

                # Extract the link
                link = title_element.get_attribute("href")

                # Append to the results
                news_items.append({"title": title, "link": link})
            except Exception as e:
                continue  # Skip articles that don't match the structure

        return news_items
    except Exception as e:
        return "I'm sorry,unable to find any news on this topic"
    finally:
        # Quit the driver
        driver.quit()

topic_function = {
    "name": "get_latest_news_from_bing",
    "description": "Get the latest news for a given topic. Call this whenever you are asked to provide the news for a topic. If no topic is provided, use World as a topic.",
    "parameters": {
        "type": "object",
        "properties": {
            "topic": {
                "type": "string",
                "description": "The topic that the user would like to get the latest news on",
            },
        },
        "required": ["topic"],
        "additionalProperties": False
    }
}

tools = [{"type": "function", "function": topic_function}]


def chat(message, history):
    messages = [{"role": "system", "content": system_message}] + history + [{"role": "user", "content": message}]
    response = openai.chat.completions.create(model=MODEL, messages=messages, tools=tools)

    if response.choices[0].finish_reason == "tool_calls":
        message = response.choices[0].message
        response, topic = handle_tool_call(message)
        messages.append(message)
        messages.append(response)
        response = openai.chat.completions.create(model=MODEL, messages=messages)

    return response.choices[0].message.content

def handle_tool_call(message):
    tool_call = message.tool_calls[0]
    arguments = json.loads(tool_call.function.arguments)
    topic = arguments.get('topic')
    latest_news = get_latest_news_from_bing(topic)
    response = {
        "role": "tool",
        "content": json.dumps({"topic": topic,"latest_news": latest_news}),
        "tool_call_id": message.tool_calls[0].id
    }
    return response, topic

gr.ChatInterface(fn=chat, type="messages").launch()
