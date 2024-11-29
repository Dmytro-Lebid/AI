import streamlit as st
from openai import OpenAI

# Set up the Streamlit app
st.title("Email Title Generator")

# Create a text area for the email content
user_prompt = st.text_area("Paste your email text below:", height=300, placeholder="Enter the content of your email here...")

system_prompt = "You are an assistant that analyzes the contents of an email \
and creates a short but meaningful email title"

# Initialize session state for the API key
if "api_key" not in st.session_state:
    st.session_state["api_key"] = None

# Function to call OpenAI API to generate email title
def generate_title():
    openai = OpenAI(api_key = st.session_state["api_key"])
    messages_for =     [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    response = openai.chat.completions.create(
        model = "gpt-4o-mini",
        messages = messages_for)
    return response.choices[0].message.content

# Add a button to generate the email title
if st.button("Generate Title"):
    if not st.session_state["api_key"]:
        st.warning("OpenAI API Key is required. Please enter it below.")
    else:
        st.session_state["email_title"] = generate_title()
        st.info("Email title generated successfully!")

# Create a smaller text area for the generated email title
title_text = st.text_input("Proposed Email Title:", placeholder="Your email title will appear here...", key="email_title")

# Display visual check for API key
st.title("API Key Management")

# Input text box to provide API Key
api_key_input = st.text_input("Enter API Key:", key="api_key_input", type="password", placeholder="Paste your API Key here")

# Button to save the API Key
if st.button("Add API Key"):
    if not api_key_input:
        st.warning("No API key was found")
    elif not api_key_input.startswith("sk-proj-"):
        st.warning("An API key was found, but it doesn't start sk-pstreroj-;"
              "please check you're using the right key")
    elif api_key_input.strip() != api_key_input:
        st.warning("An API key was found, but it looks like it might have space or "
              "tab characters at the start or end - please remove them")
    else:
        st.session_state["api_key"] = api_key_input

if st.session_state["api_key"]:
    st.success("API Key is provided!")
else:
    st.warning("API Key is not provided!")
