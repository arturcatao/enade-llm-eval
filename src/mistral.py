import os
import base64

from dotenv import load_dotenv
from mistralai.client import Mistral


load_dotenv()

API_KEY = os.getenv("MISTRAL_API_KEY")

client = Mistral(api_key=API_KEY)

MODEL = "mistral-medium-latest"


SCHEMA_RESULTADO = {
    "type": "json_schema",
    "json_schema": {
        "name": "resultado_questao",
        "schema": {
            "type": "array",
            "prefixItems": [
                {
                    "type": "integer"
                },
                {
                    "type": "string",
                    "enum": ["SIM", "NAO"]
                },
                {
                    "type": "string",
                    "enum": ["SIM", "NAO"]
                },
                {
                    "type": "string",
                    "enum": ["SIM", "NAO"]
                },
                {
                    "type": "string",
                    "enum": ["SIM", "NAO"]
                },
                {
                    "type": ["string", "null"],
                    "enum": ["SIM", "NAO", None]
                },
                {
                    "type": "string"
                }
            ],
            "minItems": 7,
            "maxItems": 7
        }
    }
}


def imagem_para_base64(caminho_imagem: str) -> str:
    """
    Lê uma imagem local e converte para Base64.
    """

    with open(caminho_imagem, "rb") as arquivo:
        imagem_bytes = arquivo.read()

    imagem_base64 = base64.b64encode(imagem_bytes).decode("utf-8")

    return imagem_base64


def avaliar(prompt: str, caminho_imagem: str | None = None) -> str:

    content = [
        {
            "type": "text",
            "text": prompt,
        }
    ]

    if caminho_imagem:

        imagem_base64 = imagem_para_base64(caminho_imagem)

        content.append(
            {
                "type": "image_url",
                "image_url": f"data:image/png;base64,{imagem_base64}",
            }
        )

    try:
        response = client.chat.complete(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "content": content
                }
            ],
            temperature=0.0,
            response_format=SCHEMA_RESULTADO,
        )

        print("  Resposta recebida do Mistral!")

        return response.choices[0].message.content

    except Exception as erro:
        print(f"  Erro na API do Mistral: {erro}")
        raise