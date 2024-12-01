import streamlit as st
import random
import openai
import ollama

# UI: Get API Key and Topic
st.title("ChatGPT vs Llama: Debate Club")
openai_api_key = st.text_input("Enter your OpenAI API key:", type="password")
topic = st.text_input("Enter a discussion topic:")

if openai_api_key and topic:
    # Randomly assign roles
    bots = ["ChatGPT", "Ollama"]
    random.shuffle(bots)
    defender, challenger = bots

    st.write(f"**{defender} will defend the topic, and {challenger} will challenge it. Invoking AI API...**")

    # Dialogue handling
    system_prompt = """
                    This is a game of debate club.
                    You will receive a topic and debate it against another chatbot.
                    You will be presented with the arguments from another chatbot and respond with yours.
                    Response max 50 words.
                    Use informal tone.
                    """
    initial_prompt = f"The topic is: {topic}"

    def generate_messages(user_prompt, role):
        if user_prompt == "":
            user_prompt = "Your opponent hasn't given an opinion yet. You start the discussion."
        else:
            user_prompt = f"Your opponent statement is: {user_prompt}"
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{initial_prompt}. Your role is the {role} of this topic. {user_prompt}"}
                ]

    def call_ollama(message):
        try:
            role = "Defender" if defender == "Ollama" else "Challenger"
            response = ollama.chat(model="llama3.2", messages=generate_messages(message, role))
            return response['message']['content']
        except Exception as e:
            return f"Error from Ollama API: {e}"

    def call_gpt(message):
        try:
            openai.api_key = openai_api_key
            role = "Defender" if defender == "ChatGPT" else "Challenger"
            response = openai.chat.completions.create(model="gpt-4o-mini", messages=generate_messages(message, role))
            return response.choices[0].message.content
        except Exception as e:
            return f"Error from OpenAI API: {e}"

    # Function to get response based on bot type
    def get_response(bot, message):
        if bot == "Ollama":
            return call_ollama(message)
        else:
            return call_gpt(message)

    # Debate loop
    messages = []
    last_message = ""

    for i in range(8):
        current_bot = defender if i % 2 == 0 else challenger
        response = get_response(current_bot, last_message)
        messages.append({"bot": current_bot, "message": response})
        last_message = response

    # Display the dialogue
    st.subheader("Debate Dialogue")
    for msg in messages:
        st.write(f"**{msg['bot']}**: {msg['message']}")