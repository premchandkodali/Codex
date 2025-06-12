import openai
import faiss
import numpy as np
import os
from openai import OpenAI
from dotenv import load_dotenv
import google.generativeai as genai
import requests

load_dotenv()
genai.configure(api_key='AIzaSyAMU14HK0RwNFhSsEtIaqoBSOOxP1Y6l6Y')
model_ai = genai.GenerativeModel("gemini-pro")
GEMINI_API_KEY = "AIzaSyAMU14HK0RwNFhSsEtIaqoBSOOxP1Y6l6Y"

from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

def get_embedding(text):
    return model.encode(text).tolist()




load_dotenv()


GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

def embed_and_search(chunks, question, k=3):
    # 1. Embed chunks
    embeddings = [get_embedding(c) for c in chunks]
    dim = len(embeddings[0])

    # 2. Index with FAISS
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(embeddings).astype('float32'))

    # 3. Embed the question and search
    q_embed = get_embedding(question)
    _, indices = index.search(np.array([q_embed]).astype('float32'), k)

    # 4. Build context
    context = '\n'.join([chunks[i] for i in indices[0]])

    # 5. Prepare prompt
    prompt = f"""Use the context below to answer the question clearly.

    Context:
    {context}

    Question:
    {question}
    """

    # 6. Call Gemini via POST request
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}]
            }
        ]
    }

    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(GEMINI_URL, headers=headers, json=payload)
    result = response.json()

    try:
        return result['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print("Gemini error:", result)
        return "No response from Gemini"
