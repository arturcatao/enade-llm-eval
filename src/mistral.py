import os
import time
import base64

from dotenv import load_dotenv
from mistralai.client import Mistral


load_dotenv()

API_KEY = os.getenv("MISTRAL_API_KEY")

client = Mistral(api_key=API_KEY)

MODEL = "mistral-medium-latest"

# ------------------------------------------
# Configuração do retry com backoff exponencial
# ------------------------------------------
MAX_TENTATIVAS = 6
ESPERA_INICIAL_SEGUNDOS = 15

# Pequena pausa fixa antes de cada chamada, para reduzir a chance de
# disparar o rate limit em primeiro lugar (em vez de só reagir a ele
# depois que ele já aconteceu).
PAUSA_ENTRE_CHAMADAS_SEGUNDOS = 3


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


def _erro_e_rate_limit(erro: Exception) -> bool:
    """
    Detecta, de forma simples, se um erro da API foi causado por
    rate limiting (HTTP 429), olhando o texto da exceção. Evita
    depender de uma classe de exceção específica da biblioteca.
    """

    mensagem = str(erro).lower()

    return (
        "429" in mensagem
        or "rate limit" in mensagem
        or "rate_limit" in mensagem
        or "too many requests" in mensagem
    )


def avaliar(prompt: str, caminho_imagem: str | None = None) -> str:

    # Pausa fixa antes de qualquer chamada, para espaçar as requisições
    # e reduzir a chance de atingir o rate limit logo de cara.
    time.sleep(PAUSA_ENTRE_CHAMADAS_SEGUNDOS)

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

    ultimo_erro: Exception | None = None

    for tentativa in range(1, MAX_TENTATIVAS + 1):

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

            return response.choices[0].message.content

        except Exception as erro:

            ultimo_erro = erro

            if _erro_e_rate_limit(erro) and tentativa < MAX_TENTATIVAS:

                espera = ESPERA_INICIAL_SEGUNDOS * (2 ** (tentativa - 1))

                print(
                    f"  Rate limit atingido (tentativa "
                    f"{tentativa}/{MAX_TENTATIVAS}). "
                    f"Aguardando {espera}s antes de tentar novamente..."
                )

                time.sleep(espera)
                continue

            print(f"  Erro na API do Mistral: {erro}")
            raise

    # Não deveria chegar aqui, mas por segurança:
    raise ultimo_erro