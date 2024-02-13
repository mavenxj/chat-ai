import openai
import time
import streamlit as st
from langchain_community.llms import OpenAI
from langchain.embeddings.openai import OpenAIEmbeddings

st.title('AI Chatbot')
openai_api_key = st.sidebar.text_input('OpenAI API Key')

limit = 3750
openai.api_key = openai_api_key
model_name = 'gpt-3.5-turbo-0613'

def complete(prompt):
    # instructions
    sys_prompt = "You are a helpful assistant that always answers questions."
    res = openai.ChatCompletion.create(
        model=model_name,
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
    return res['choices'][0]['message']['content'].strip()
  
def generate_response(input_text):
  response = complete(input_text)
  st.info(response)

with st.form('my_form'):
  query = 'What is Artificial Intelligence?'
  text = st.text_area('Enter text:', query)
  submitted = st.form_submit_button('Submit')
  if not openai_api_key.startswith('sk-'):
    st.warning('Please enter your OpenAI API key!', icon='⚠')
  if submitted and openai_api_key.startswith('sk-'):
    generate_response(text)
