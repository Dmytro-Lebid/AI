# imports to retreive news articles
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# imports to run application and AI API
import os
import json
from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr
import time

# imports for image generation
import base64
from io import BytesIO
from PIL import Image

# imports for audio generation
import tempfile
import subprocess
from pydub import AudioSegment
import time
import threading

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
system_message += "Limit articles to 4 max."
system_message += "Use max 100 words"

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
        WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.news-card")))

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


def chat(history):
    messages = [{"role": "system", "content": system_message}] + history
    response = openai.chat.completions.create(model=MODEL, messages=messages, tools=tools)
    image = None

    if response.choices[0].finish_reason == "tool_calls":
        message = response.choices[0].message
        response, latest_news = handle_tool_call(message)
        messages.append(message)
        messages.append(response)
        image = artist(latest_news)
        response = openai.chat.completions.create(model=MODEL, messages=messages)

    reply = response.choices[0].message.content
    history += [{"role": "assistant", "content": reply}]

    audio_thread = threading.Thread(target=talker, args=(reply,))
    audio_thread.start()

    return history, image

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
    return response, latest_news

def artist(news):
    image_response = openai.images.generate(
            model="dall-e-3",
            prompt=f"Create image as illustration to the following news: {news}. "
                   f"Adjust the style of image to the content. "
                   f"For example, for sad news use darker color, for happy news use more vibrant colors.",
            size="1024x1024",
            n=1,
            response_format="b64_json",
        )
    image_base64 = image_response.data[0].b64_json
    image_data = base64.b64decode(image_base64)
    return Image.open(BytesIO(image_data))


def play_audio(audio_segment):
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, "temp_audio.wav")
    try:
        audio_segment.export(temp_path, format="wav")
        time.sleep(
            3)  # Student Dominic found that this was needed. You could also try commenting out to see if not needed on your PC
        subprocess.call([
            "ffplay",
            "-nodisp",
            "-autoexit",
            "-hide_banner",
            temp_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    finally:
        try:
            os.remove(temp_path)
        except Exception:
            pass

def talker(message):
    response = openai.audio.speech.create(
        model="tts-1",
        voice="onyx",  # Also, try replacing onyx with alloy
        input=message
    )
    audio_stream = BytesIO(response.content)
    audio = AudioSegment.from_file(audio_stream, format="mp3")
    play_audio(audio)

with gr.Blocks() as ui:
    with gr.Row():
        chatbot = gr.Chatbot(height=500, type="messages")
        image_output = gr.Image(height=500)
    with gr.Row():
        entry = gr.Textbox(label="Chat with our AI Assistant:")
    with gr.Row():
        clear = gr.Button("Clear")

    def do_entry(message, history):
        history += [{"role":"user", "content":message}]
        return "", history

    entry.submit(do_entry, inputs=[entry, chatbot], outputs=[entry, chatbot]).then(
        chat, inputs=chatbot, outputs=[chatbot, image_output]
    )
    clear.click(lambda: None, inputs=None, outputs=chatbot, queue=False)

ui.launch(inbrowser=True)

