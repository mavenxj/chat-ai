import openai
import time
import streamlit as st
#from langchain.llms import OpenAI
from langchain_community.llms import OpenAI
from langchain.embeddings.openai import OpenAIEmbeddings

import pinecone_datasets
dataset = pinecone_datasets.load_dataset('wikipedia-simple-text-embedding-ada-002-100K')

# we drop sparse_values as they are not needed for this example
dataset.documents.drop(['metadata'], axis=1, inplace=True)
dataset.documents.rename(columns={'blob': 'metadata'}, inplace=True)

import os
from pinecone import Pinecone
from pinecone import ServerlessSpec, PodSpec
import time

st.title('AI Chatbot')
openai_api_key = st.sidebar.text_input('OpenAI API Key')
pine_api_key = st.sidebar.text_input('Pinecone API Key')

# configure client
pc = Pinecone(api_key=pine_api_key)
environment = 'gcp-starter'
use_serverless = False

if use_serverless:
    spec = ServerlessSpec(cloud='aws', region='us-west-2')
else:
    # if not using a starter index, you should specify a pod_type too
    spec = PodSpec(environment=environment)

# check for and delete index if already exists
index_name = 'index-llm'
if index_name in pc.list_indexes().names():
    pc.delete_index(index_name)

# we create a new index
pc.create_index(
        index_name,
        dimension=1536,  # dimensionality of text-embedding-ada-002
        metric='cosine',
        spec=spec
    )

# wait for index to be initialized
while not pc.describe_index(index_name).status['ready']:
    time.sleep(1)

index = pc.Index(index_name)

limit = 3750
openai.api_key = openai_api_key
model_name = 'gpt-3.5-turbo-0613'

def retrieve(query):
    res = openai.Embedding.create(
        input=[query],
        engine='text-embedding-ada-002'
    )

    # retrieve from Pinecone
    xq = res['data'][0]['embedding']

    # get relevant contexts
    contexts = []
    time_waited = 0
    while (len(contexts) < 3 and time_waited < 60 * 12):
        res = index.query(vector=xq, top_k=3, include_metadata=True)
        contexts = contexts + [
            x['metadata']['text'] for x in res['matches']
        ]
        print(f"Retrieved {len(contexts)} contexts, sleeping for 15 seconds...")
        time.sleep(15)
        time_waited += 15

    if time_waited >= 60 * 12:
        print("Timed out waiting for contexts to be retrieved.")
        contexts = ["No contexts retrieved. Try to answer the question yourself!"]


    # build our prompt with the retrieved contexts included
    prompt_start = (
        "Answer the question based on the context below.\n\n"+
        "Context:\n"
    )
    prompt_end = (
        f"\n\nQuestion: {query}\nAnswer:"
    )
    # append contexts until hitting limit
    for i in range(1, len(contexts)):
        if len("\n\n---\n\n".join(contexts[:i])) >= limit:
            prompt = (
                prompt_start +
                "\n\n---\n\n".join(contexts[:i-1]) +
                prompt_end
            )
            break
        elif i == len(contexts)-1:
            prompt = (
                prompt_start +
                "\n\n---\n\n".join(contexts) +
                prompt_end
            )
    return prompt


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
  query_with_contexts = retrieve(input_text)
  response = complete(query_with_contexts)
  st.info(response)

with st.form('my_form'):
  query = 'What is Artificial Intelligence?'
  text = st.text_area('Enter text:', query)
  submitted = st.form_submit_button('Submit')
  if not openai_api_key.startswith('sk-'):
    st.warning('Please enter your OpenAI API key!', icon='⚠')
  if submitted and openai_api_key.startswith('sk-'):
    generate_response(text)

pc.delete_index(index_name)
