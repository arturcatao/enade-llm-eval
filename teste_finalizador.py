import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY não encontrada.")

client = Groq(api_key=api_key)

print("Testando GPT-OSS 120B...")

resposta = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {
            "role": "user",
            "content": (
                "Responda somente: "
                "FINALIZADOR FUNCIONANDO"
            )
        }
    ],
    reasoning_effort="medium",
    max_completion_tokens=200
)

print(resposta.choices[0].message.content)