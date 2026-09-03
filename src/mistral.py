import os
import base64

from dotenv import load_dotenv
from mistralai.client import Mistral


load_dotenv()

API_KEY = os.getenv("MISTRAL_API_KEY")


client = Mistral(api_key=API_KEY)

MODEL = "pixtral-large-latest"


def imagem_para_base64(caminho_imagem: str) -> str:
    """
    Lê uma imagem local e converte para Base64.
    """

    with open(caminho_imagem, "rb") as arquivo:
        imagem_bytes = arquivo.read()

    imagem_base64 = base64.b64encode(imagem_bytes).decode("utf-8")

    return imagem_base64


def avaliar(prompt: str, caminho_imagem: str | None = None) -> str:
    """
    Envia o prompt e, opcionalmente, uma imagem para o Mistral.

    Retorna apenas o conteúdo textual da resposta.
    """

    content = [
        {
            "type": "text",
            "text": prompt,
        }
    ]

    # Se a questão tiver imagem, adiciona a imagem à requisição
    if caminho_imagem:
        imagem_base64 = imagem_para_base64(caminho_imagem)

        content.append(
            {
                "type": "image_url",
                "image_url": f"data:image/png;base64,{imagem_base64}",
            }
        )

    response = client.chat.complete(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": content,
            }
        ],
        temperature=0.0,
    )

    return response.choices[0].message.content