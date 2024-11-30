import streamlit as st
from openai import OpenAI

# Constants
API_KEY_PREFIX = "sk-proj"
SYSTEM_PROMPT = (
    "You are an assistant that analyzes the contents of an email "
    "and creates a short but meaningful email title."
)
MODEL_NAME = "gpt-4o-mini"

# Initialize default session state
def initialize_session_state():
    if "api_key" not in st.session_state:
        st.session_state["api_key"] = None
    if "openai_client" not in st.session_state:
        st.session_state["openai_client"] = None
    if "email_title" not in st.session_state:
        st.session_state["email_title"] = ""

# Validate API key
def validate_api_key(api_key):
    if not api_key:
        return "API key cannot be empty."
    if not api_key.startswith(API_KEY_PREFIX):
        return f"API key must start with '{API_KEY_PREFIX}'."
    if api_key != api_key.strip():
        return "API key contains leading or trailing whitespace."
    return None

# Initialize OpenAI client
def initialize_openai_client():
    if st.session_state["api_key"]:
        st.session_state["openai_client"] = OpenAI(api_key=st.session_state["api_key"])

# Generate email title
def generate_title():
    try:
        client = st.session_state["openai_client"]
        if not client:
            st.error("OpenAI client is not initialized. Please add a valid API key.")
            return None

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": st.session_state.get("user_prompt", "")}
        ]
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"An error occurred while generating the title: {str(e)}")
        return None

# App start
initialize_session_state()
st.title("Email Title Generator")

# Email input
user_prompt = st.text_area("Paste your email text below:", height=300, placeholder="Enter the content of your email here...")
st.session_state["user_prompt"] = user_prompt

# Generate button
if st.button("Generate Title"):
    if not st.session_state["api_key"]:
        st.warning("OpenAI API Key is required. Please enter it below.")
    else:
        st.session_state["email_title"] = generate_title()

# Display generated email title
st.text_input("Proposed Email Title:", value=st.session_state["email_title"], key="email_title", disabled=True)

# API Key Management
st.subheader("API Key Management")
api_key_input = st.text_input("Enter API Key:", type="password", placeholder="Paste your API Key here")
if st.button("Add API Key"):
    error = validate_api_key(api_key_input)
    if error:
        st.warning(error)
    else:
        st.session_state["api_key"] = api_key_input
        initialize_openai_client()
        st.success("API Key saved successfully!")