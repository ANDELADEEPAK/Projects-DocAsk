import os

from dotenv import load_dotenv
from google import genai
from google.genai import types


import socket

original_getaddrinfo = socket.getaddrinfo

def ipv4_only(*args, **kwargs):
    results = original_getaddrinfo(*args, **kwargs)
    return [
        item for item in results
        if item[0] == socket.AF_INET
    ]

socket.getaddrinfo = ipv4_only


load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("Gemini API key not found in .env")


client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(
        timeout=60000
    )
)


def create_embedding(text, task_type="RETRIEVAL_DOCUMENT"):

    response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
        config=types.EmbedContentConfig(
            task_type=task_type
        )
    )

    return response.embeddings[0].values