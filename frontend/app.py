import streamlit as st
import requests
import os
import sys

# --- Add project root to sys.path ---
# Necessary if Streamlit runs from a different CWD
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# --- End path modification ---

# --- Configuration ---
BACKEND_URL = "http://127.0.0.1:8000/chat" # URL of our FastAPI endpoint

# --- Streamlit App ---

st.set_page_config(page_title="Project Samarth Q&A", layout="wide")
st.title("🇮🇳 Project Samarth: Agri & Price Q&A Agent")
st.caption("Ask complex questions about Indian agricultural production and market prices.")

# --- Initialize chat history ---
# We store text content for history, display handles images separately
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Display chat messages from history ---
# Note: History only stores text. Images are displayed live during generation.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Accept user input ---
if prompt := st.chat_input("Ask a question..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- Get response from backend ---
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        image_placeholder = st.empty() # Placeholder specifically for the image
        full_response_text = ""
        image_base64 = None # Initialize image data variable

        # Display a loading indicator while waiting
        with st.spinner("Agent is thinking..."):
            try:
                # Prepare the request payload
                payload = {"query": prompt}

                # Send the request to the FastAPI backend
                response = requests.post(BACKEND_URL, json=payload, timeout=600) # Increased timeout
                response.raise_for_status() # Raise an exception for bad status codes

                # Get the answer and potential image from the JSON response
                answer_data = response.json()
                full_response_text = answer_data.get("answer", "Sorry, I couldn't get a response.")
                image_base64 = answer_data.get("image_base64")

            except requests.exceptions.Timeout:
                 full_response_text = "Error: The request timed out. The agent might be taking too long."
            except requests.exceptions.RequestException as e:
                full_response_text = f"Error connecting to the backend: {e}"
            except Exception as e:
                 full_response_text = f"An unexpected error occurred: {e}"

        # Display text response first
        message_placeholder.markdown(full_response_text)

        # Display image if it exists
        if image_base64:
            try:
                # Construct the data URI carefully
                image_data_uri = f"data:image/png;base64,{image_base64.strip()}" # Add .strip() just in case
                image_placeholder.image(image_data_uri, caption="Generated Plot")
            except Exception as img_e:
                image_placeholder.error(f"Failed to display image: {img_e}")


    # Add assistant response (text only) to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response_text})