import os
from dotenv import load_dotenv

# Import AI models API
from openai import OpenAI
import google.generativeai
import anthropic
import ollama

import gradio as gr

def load_api_keys():
    load_dotenv()
    openai_api_key = os.getenv('OPENAI_API_KEY')
    anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
    google_api_key = os.getenv('GOOGLE_API_KEY')

    if openai_api_key:
        print(f"OpenAI API Key exists and begins {openai_api_key[:8]}")
    else:
        print("OpenAI API Key not set")

    if anthropic_api_key:
        print(f"Anthropic API Key exists and begins {anthropic_api_key[:7]}")
    else:
        print("Anthropic API Key not set")

    if google_api_key:
        print(f"Google API Key exists and begins {google_api_key[:8]}")
    else:
        print("Google API Key not set")

def messages_for(system_message, prompt):
    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": prompt}
      ]

def stream_gpt(system_message, prompt):
    stream = openai.chat.completions.create(
        model='gpt-4o-mini',
        messages=messages_for(system_message, prompt),
        stream=True
    )
    result = ""
    for chunk in stream:
        result += chunk.choices[0].delta.content or ""
        yield result

def stream_claude(system_message, prompt):
    result = claude.messages.stream(
        model="claude-3-haiku-20240307",
        max_tokens=1000,
        temperature=0.7,
        system=system_message,
        messages=[
            {"role": "user", "content": prompt},
        ],
    )
    response = ""
    with result as stream:
        for text in stream.text_stream:
            response += text or ""
            yield response

def stream_gemini(system_message, prompt):
    gemini = google.generativeai.GenerativeModel(
        model_name='gemini-1.5-flash',
        system_instruction=system_message
    )
    response = gemini.generate_content(prompt)
    for chunk in response:
        yield chunk.text

def stream_ollama(system_message, prompt):
    stream = ollama.chat(
        model=MODEL,
        messages=messages_for(system_message, prompt),
        stream = True
    )
    result = ""
    for chunk in stream:
        result += chunk['message']['content'] or ""
        yield result

def stream_model(prompt, model, tone):
    system_message = f"You are a helpful assistant. Use {tone} tone in your responses. Respond in Markdown."

    if model=="Claude":
        result = stream_claude(system_message, prompt)
    elif model=="Gemini":
        result = stream_gemini(system_message, prompt)
    elif model=="GPT":
        result = stream_gpt(system_message, prompt)
    elif model=="Ollama":
        result = stream_ollama(system_message, prompt)
    else:
        raise ValueError("Unknown model")
    yield from result

# Program execution
load_api_keys()
# Connect to AI APIs
openai = OpenAI()
claude = anthropic.Anthropic()
google.generativeai.configure()
#
MODEL = "llama3.2"
FORCE_DARK_MODE = """
function refresh() {
    const url = new URL(window.location);
    if (url.searchParams.get('__theme') !== 'dark') {
        url.searchParams.set('__theme', 'dark');
        window.location.href = url.href;
    }
}
"""

view = gr.Interface(
    fn=stream_model,
    inputs=[
        gr.Textbox(label="Your message:"),
        gr.Dropdown(["Claude", "Gemini", "GPT", "Ollama"], label="Select model", value="GPT"),
        gr.Dropdown(["angry", "ironic", "official", "sad"], label="Select tone", value="official")
    ],
    outputs=[gr.Markdown(label="Response:")],
    flagging_mode="never",
    js=FORCE_DARK_MODE
)
view.launch()

