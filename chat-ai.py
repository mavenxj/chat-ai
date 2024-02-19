import google.generativeai as genai
import streamlit as st
import re
import os
import io
import PIL.Image
import urllib.request as urllib
from pathlib import Path
from gtts import gTTS

def main():
    # Customize the layout of chatbot
    st.set_page_config(page_title="Generative AI", layout="wide")
    st.title("AI Bot")

    GOOGLE_API_KEY = st.sidebar.text_input("Google API Key", type="password", key="K1")
    os.environ['GOOGLE_API_KEY'] = GOOGLE_API_KEY

    col1, col2 = st.columns(2, gap="medium")

    with col1:
        st.header("Query")
        if not os.getenv('GOOGLE_API_KEY', '').startswith("AI"):
            st.warning("Note: Enter your Google API key in the sidebar.")
        
        # Initialize the GenAI
        genai.configure(api_key=GOOGLE_API_KEY)

        question = st.text_input("Prompt", key="K-text")

        img = ""    
        image_url = st.text_input("Image URL", key="K-img")

        #read image file
        if image_url:
            fd = urllib.urlopen(image_url)
            image_file = io.BytesIO(fd.read())
            img = PIL.Image.open(image_file)
            st.image(image_url)

    with col2:
        st.header("Response")
        
        # text generation
        if img:
            out1 = get_response_image(question, img)
            # speech conversion
            TTS(out1)
            st.write(out1) 
        elif not question == "":
            out2 = get_response_text(question)
            # speech conversion
            TTS(out2)
            st.write(out2)

def get_response_image(query, image):
    model = genai.GenerativeModel('gemini-pro-vision')
    response = model.generate_content([query, image], stream=True)
    response.resolve()
    res_img = response.text
    return res_img

def get_response_text(query):
    model = genai.GenerativeModel('gemini-pro')
    chat = model.start_chat(history=[])
    response = chat.send_message(query, stream=True)
    response.resolve()
    res_text = response.text
    return res_text

#text to speech
def TTS(res):
    # remove special characters before speech conversion
    spl_char = '[^a-zA-Z0-9%&$ \n\.]'
    clean_text = re.sub(pattern=spl_char, repl="", string=res)

    tts = gTTS(text=clean_text, lang='en')
    filename = 'response.wav'
    tts.save(filename)

    _dir = Path(__file__).parent
    audio_path = _dir / filename
    os.environ['AUDIO_KEY'] = str(audio_path)
        
    try:
        audio_file = open(os.environ['AUDIO_KEY'], 'rb')
        audio_bytes = audio_file.read()
        st.write("Listen to the text.")
        st.audio(audio_bytes, format='audio/wav')
    except(FileNotFoundError) :
        st.error("File not found")

if __name__ == "__main__":
  main()
