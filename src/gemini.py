import os
import json
import time
import mimetypes

from dotenv import load_dotenv
from google import genai
from google.genai import types


load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=API_KEY)

# Modelos "Flash" atuais com free tier na Google AI Studio. Se este
# não estiver disponível na sua conta, confira em aistudio.google.com
# quais modelos aparecem como gratuitos e troque aqui (ex.:
# "gemini-3.8-flash", "gemini-2.5-flash").
#MODEL = "gemini-3.5-flash"
MODEL = "gemini-3.6-flash"

# ------------------------------------------
# Configuração do retry com backoff exponencial
# ------------------------------------------
MAX_TENTATIVAS = 6
ESPERA_INICIAL_SEGUNDOS = 15
ESPERA_MAXIMA_SEGUNDOS = 300  # nunca espera mais que 5 minutos

# Pequena pausa fixa antes de cada chamada, para reduzir a chance de
# disparar o rate limit em primeiro lugar (em vez de só reagir a ele
# depois que ele já aconteceu).
PAUSA_ENTRE_CHAMADAS_SEGUNDOS = 3


# O Gemini usa um subconjunto do OpenAPI 3.0 pra response_schema, que
# não suporta "tupla heterogênea" (prefixItems) como o json_schema do
# Mistral suportava. Por isso pedimos um OBJETO com 7 campos nomeados,
# e depois convertemos para a mesma lista de 7 posições que o
# parser.py já espera — assim main.py e parser.py não precisam mudar
# nada.
SCHEMA_RESULTADO = {
    "type": "OBJECT",
    "properties": {
        "numero_da_questao": {"type": "INTEGER"},
        "se_acertou": {"type": "STRING", "enum": ["SIM", "NAO"]},
        "explicacao_ta_boa": {"type": "STRING", "enum": ["SIM", "NAO"]},
        "sem_rastro_llm": {"type": "STRING", "enum": ["SIM", "NAO"]},
        "acordo_com_inep": {"type": "STRING", "enum": ["SIM", "NAO"]},
        "anulada_tem_explicacao": {
            "type": "STRING",
            "enum": ["SIM", "NAO"],
            "nullable": True,
        },
        "explicacao_final": {"type": "STRING"},
    },
    "required": [
        "numero_da_questao",
        "se_acertou",
        "explicacao_ta_boa",
        "sem_rastro_llm",
        "acordo_com_inep",
        "explicacao_final",
    ],
}


def _erro_e_rate_limit(erro: Exception) -> bool:
    """
    Detecta, de forma simples, se um erro da API foi causado por
    rate limiting / cota excedida, olhando o texto da exceção. Evita
    depender de uma classe de exceção específica do SDK.
    """

    mensagem = str(erro).lower()

    return (
        "429" in mensagem
        or "resource_exhausted" in mensagem
        or "quota" in mensagem
        or "rate limit" in mensagem
        or "rate_limit" in mensagem
        or "too many requests" in mensagem
    )


def _mime_type_da_imagem(caminho_imagem: str) -> str:
    tipo, _ = mimetypes.guess_type(caminho_imagem)
    return tipo or "image/png"


def _objeto_para_lista(objeto: dict) -> list:
    """
    Converte o objeto JSON retornado pelo Gemini na mesma lista de 7
    posições que o parser.py já espera (idêntica ao formato que o
    Mistral retornava).
    """

    return [
        objeto.get("numero_da_questao"),
        objeto.get("se_acertou"),
        objeto.get("explicacao_ta_boa"),
        objeto.get("sem_rastro_llm"),
        objeto.get("acordo_com_inep"),
        objeto.get("anulada_tem_explicacao"),
        objeto.get("explicacao_final"),
    ]


def avaliar(prompt: str, caminho_imagem: str | None = None) -> str:

    # Pausa fixa antes de qualquer chamada, para espaçar as requisições
    # e reduzir a chance de atingir o rate limit logo de cara.
    time.sleep(PAUSA_ENTRE_CHAMADAS_SEGUNDOS)

    conteudo = [prompt]

    if caminho_imagem:

        with open(caminho_imagem, "rb") as arquivo:
            imagem_bytes = arquivo.read()

        conteudo.append(
            types.Part.from_bytes(
                data=imagem_bytes,
                mime_type=_mime_type_da_imagem(caminho_imagem),
            )
        )

    config = types.GenerateContentConfig(
        temperature=0.0,
        response_mime_type="application/json",
        response_schema=SCHEMA_RESULTADO,
    )

    ultimo_erro: Exception | None = None
    tentativa = 1

    while tentativa <= MAX_TENTATIVAS:

        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=conteudo,
                config=config,
            )

            objeto = json.loads(response.text)
            lista_resultado = _objeto_para_lista(objeto)

            # Devolve no mesmo formato que o parser.py espera: uma
            # string contendo um array JSON de 7 posições.
            return json.dumps(lista_resultado, ensure_ascii=False)

        except Exception as erro:

            ultimo_erro = erro

            if _erro_e_rate_limit(erro) and tentativa < MAX_TENTATIVAS:

                espera = min(
                    ESPERA_INICIAL_SEGUNDOS * (2 ** (tentativa - 1)),
                    ESPERA_MAXIMA_SEGUNDOS,
                )

                print(
                    f"  Rate limit atingido (tentativa "
                    f"{tentativa}/{MAX_TENTATIVAS}). "
                    f"Aguardando {espera}s antes de tentar novamente..."
                )

                time.sleep(espera)
                tentativa += 1
                continue

            print(f"  Erro na API do Gemini: {erro}")
            raise

    raise ultimo_erro