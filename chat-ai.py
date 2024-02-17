import google.generativeai as genai
import streamlit as st
import os
import io
import PIL.Image
import urllib.request as urllib
from pathlib import Path
from gtts import gTTS
import time
import keyboard
import psutil

def main():
    # Customize the layout of chatbot
    st.set_page_config(page_title="Generative AI", layout="wide")
    st.title("AI Bot")

    GOOGLE_API_KEY = st.sidebar.text_input("Google API Key", type="password", key="K1")
    os.environ['GOOGLE_API_KEY'] = GOOGLE_API_KEY

    if not os.getenv('GOOGLE_API_KEY', '').startswith("AI"):
        st.warning("Note: Enter your Google API key for this chat.")

    # Initialize the GenAI
    genai.configure(api_key=GOOGLE_API_KEY)

    img = ""    
    image_url = st.sidebar.text_input("Enter image url:", key="K-img")

    question = st.text_input("How can the AI assistant assist you today...")
                             
    #read image file
    if image_url:
        fd = urllib.urlopen(image_url)
        image_file = io.BytesIO(fd.read())
        img = PIL.Image.open(image_file)
        st.image(image_url, width=500)

    # Query through AI
    if img:
        get_response_image(question, img)
    elif not question == "":
        get_response_text(question)

    exit_app = st.sidebar.button("Logout")

    if exit_app:
        # Give a bit of delay for user experience
        time.sleep(3)
    
        # Close streamlit browser tab
        keyboard.press_and_release('ctrl+w')

        # Terminate streamlit python process
        pid = os.getpid()
        p = psutil.Process(pid)
        p.terminate()

def get_response_image(query, image):
    model = genai.GenerativeModel('gemini-pro-vision')
    response = model.generate_content([query, image], stream=True)
    response.resolve()
    out = response.text
    st.write(out)
    TTS(out)

#generative AI for text input
def get_response_text(query):
    model = genai.GenerativeModel('gemini-pro')
    chat = model.start_chat()
    response = chat.send_message(query, stream=True)
    response.resolve()
    out = response.text
    st.write(out)
    TTS(out)

# text to speech
def TTS(response_ai):
    # Convert TTS button
    if st.button("Convert to Speech"):
        tts = gTTS(text = response_ai, lang='en')
        filename = 'response.wav'
        tts.save(filename)

        _dir = Path(__file__).parent
        audio_path = _dir / filename
        os.environ['AUDIO_KEY'] = str(audio_path)

        try:
            audio_file = open(os.environ['AUDIO_KEY'], 'rb')
            audio_bytes = audio_file.read()
            st.audio(audio_bytes, format='audio/wav')
        except(FileNotFoundError) :
            st.error("File not found")

if __name__ == "__main__":
  main()
