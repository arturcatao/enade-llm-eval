import os

from dotenv import load_dotenv
from mistralai.client import Mistral

load_dotenv()

API_KEY = os.getenv("MISTRAL_API_KEY")

print("API key encontrada:", bool(API_KEY))

client = Mistral(
    api_key=API_KEY,
    timeout_ms=30000
)

print("Enviando teste...")

response = client.chat.complete(
    model="mistral-medium-latest",
    messages=[
        {
            "role": "user",
            "content": "Responda apenas: OK"
        }
    ],
    temperature=0.0,
)

print("Resposta:")
print(response.choices[0].message.content)