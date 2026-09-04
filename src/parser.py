import json


VALORES_SIM_NAO = {"SIM", "NAO"}
VALORES_ANULADA = {"SIM", "NAO", None}


def limpar_resposta(resposta: str) -> str:
    resposta = resposta.strip()

    if resposta.startswith("```"):
        linhas = resposta.splitlines()

        if linhas and linhas[0].strip().startswith("```"):
            linhas = linhas[1:]

        if linhas and linhas[-1].strip() == "```":
            linhas = linhas[:-1]

        resposta = "\n".join(linhas).strip()

    return resposta


def parsear_resposta(resposta: str) -> list:
    resposta = limpar_resposta(resposta)

    try:
        resultado = json.loads(resposta)
    except json.JSONDecodeError as erro:
        raise ValueError(
            f"Resposta do Mistral não está em um JSON válido:\n"
            f"{resposta}"
        ) from erro

    if not isinstance(resultado, list):
        raise ValueError(
            f"A resposta do Mistral deveria ser uma lista, "
            f"mas recebeu {type(resultado).__name__}."
        )

    if len(resultado) != 7:
        raise ValueError(
            f"A resposta deveria ter 7 elementos, "
            f"mas possui {len(resultado)}."
        )

    return resultado


def validar_resultado(resultado: list) -> list:

    numero = resultado[0]
    se_acertou = resultado[1]
    explicacao_ta_boa = resultado[2]
    sem_rastro_llm = resultado[3]
    acordo_com_inep = resultado[4]
    anulada_tem_explicacao = resultado[5]
    explicacao_final = resultado[6]

    if not isinstance(numero, int) or isinstance(numero, bool):
        raise ValueError(
            "numero_da_questao deve ser um inteiro."
        )

    campos_sim_nao = {
        "se_acertou": se_acertou,
        "explicacao_ta_boa": explicacao_ta_boa,
        "sem_rastro_llm": sem_rastro_llm,
        "acordo_com_inep": acordo_com_inep,
    }

    for nome, valor in campos_sim_nao.items():

        if valor not in VALORES_SIM_NAO:
            raise ValueError(
                f"{nome} deve ser 'SIM' ou 'NAO', "
                f"mas recebeu: {valor}"
            )

    if anulada_tem_explicacao not in VALORES_ANULADA:
        raise ValueError(
            "anulada_tem_explicacao deve ser "
            "'SIM', 'NAO' ou null."
        )

    if not isinstance(explicacao_final, str):
        raise ValueError(
            "explicacao_final deve ser uma string."
        )

    if not explicacao_final.strip():
        raise ValueError(
            "explicacao_final não pode estar vazia."
        )

    return resultado


def processar_resposta(resposta: str) -> list:
    resultado = parsear_resposta(resposta)
    return validar_resultado(resultado)