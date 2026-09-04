import os
import pandas as pd

from prompt import montar_prompt
from images import buscar_imagem
from mistral import avaliar
from parser import processar_resposta


ARQUIVO_QUESTOES = "../data/2021/Enade2021-Questões.csv"
ARQUIVO_GABARITO = "../data/2021/Enade2021-GabaritoFinal.csv"
ARQUIVO_SAIDA = "../data/resultados.csv"

COLUNAS_RESULTADO = [
    "numero_da_questao",
    "se_acertou",
    "explicacao_ta_boa",
    "sem_rastro_llm",
    "acordo_com_inep",
    "anulada_tem_explicacao",
    "explicacao_final"
]


# ==================================================
# HELPERS: leitura de colunas e valores
# ==================================================

def _primeiro_valor(questao, nomes_candidatos):
    """
    Procura, em ordem, pelo primeiro nome de coluna existente em
    `questao` (uma linha do DataFrame já mesclado) cujo valor não seja
    nulo. Isso lida com o fato de que algumas colunas podem ganhar
    sufixos "_questao"/"_gabarito" após o merge, caso existam nos dois
    CSVs.

    Retorna None se nenhuma delas existir ou todas estiverem vazias.
    """

    for nome in nomes_candidatos:
        if nome in questao.index and pd.notna(questao[nome]):
            valor = questao[nome]
            if isinstance(valor, str) and valor.strip() == "":
                continue
            return valor

    return None


def _coluna_existe(questao, nomes_candidatos) -> bool:
    """
    Verifica se pelo menos uma das colunas candidatas existe no
    DataFrame (independente do valor estar preenchido nesta linha).
    Usado para distinguir um problema estrutural (coluna não existe em
    lugar nenhum) de um valor simplesmente ausente para esta questão
    específica (o que é esperado e tratado como "resposta vazia").
    """

    return any(nome in questao.index for nome in nomes_candidatos)


def resposta_esta_vazia(valor) -> bool:
    if valor is None:
        return True
    if isinstance(valor, float) and pd.isna(valor):
        return True
    if isinstance(valor, str) and valor.strip() == "":
        return True
    return False


def extrair_dados_questao(questao) -> dict:
    """
    Centraliza, em um único lugar, a resolução de todos os dados
    objetivos da questão a partir da linha mesclada do DataFrame.
    Nenhum desses dados deve ser inferido pelo Mistral — o Python é a
    única fonte de verdade para eles.
    """

    numero = int(questao["numero_da_questao"])

    enunciado = _primeiro_valor(questao, ["Enunciado"])

    gabarito_inep = _primeiro_valor(
        questao, ["Gabarito INEP", "Gabarito INEP_questao", "Gabarito INEP_gabarito"]
    )

    # A situação do GABARITO é tratada como a situação oficial da
    # questão, conforme definido pelo projeto. Não usamos a coluna
    # "Situação" vinda da planilha de questões como fallback, pois isso
    # poderia mascarar silenciosamente uma divergência real entre as
    # duas fontes.
    situacao_oficial = _primeiro_valor(
        questao, ["Situação_gabarito", "Situação"]
    )

    # IMPORTANTE: apesar do nome, a coluna "Gabarito comentado final" é
    # onde está armazenada a RESPOSTA AVALIADA (a resposta/explicação
    # que o Mistral deve julgar) — confirmado pelo dono do projeto. Não
    # existe, separadamente, um "gabarito comentado oficial" para
    # comparação: a única referência autorizada para a alternativa
    # correta é "Gabarito INEP".
    candidatos_resposta = [
        "Gabarito comentado final",
        "Gabarito comentado final_questao",
        "Gabarito comentado final_gabarito",
    ]

    resposta_avaliada = _primeiro_valor(questao, candidatos_resposta)

    modelo_base = _primeiro_valor(
        questao,
        [
            "Modelo(s)-base",
            "Modelo(s)-base_questao",
            "Modelo(s)-base_gabarito",
        ],
    )

    if enunciado is None:
        raise ValueError(
            f"Questão {numero}: não foi possível localizar a coluna "
            f"'Enunciado' após o merge. Verifique o nome exato da "
            f"coluna nos CSVs."
        )

    # Só é um erro estrutural se a coluna não existir em NENHUMA linha
    # (nome de coluna errado / merge quebrado). Se a coluna existe mas
    # está vazia apenas para esta questão específica, isso é esperado
    # (algumas questões ainda não têm gabarito comentado final) e deve
    # ser tratado como "resposta vazia" pelo restante do pipeline, não
    # como um erro fatal.
    if not _coluna_existe(questao, candidatos_resposta):
        raise ValueError(
            f"Questão {numero}: não foi possível localizar a coluna "
            f"'Gabarito comentado final' após o merge. Esse é o campo "
            f"que contém a resposta a ser avaliada. Verifique o nome "
            f"exato da coluna no CSV de origem."
        )

    return {
        "numero": numero,
        "enunciado": str(enunciado),
        "gabarito_inep": gabarito_inep,
        "situacao_oficial": situacao_oficial,
        "resposta_avaliada": resposta_avaliada,
        "modelo_base": modelo_base,
    }


def situacao_e_anulada(situacao_oficial) -> bool:
    if situacao_oficial is None:
        return False
    return str(situacao_oficial).strip().lower() == "anulada"


def aplicar_regras_deterministicas(resultado: list, dados: dict) -> list:
    """
    Sobrescreve, no lado do Python, os campos que dependem de fatos
    objetivos já conhecidos (resposta ausente, gabarito INEP ausente,
    situação oficial da questão). Isso garante que o Mistral NUNCA
    consiga, por alucinação, contornar essas regras — mesmo que o
    prompt seja ignorado ou mal interpretado pelo modelo.
    """

    resposta_vazia = resposta_esta_vazia(dados["resposta_avaliada"])
    gabarito_ausente = resposta_esta_vazia(dados["gabarito_inep"])
    anulada = situacao_e_anulada(dados["situacao_oficial"])

    if resposta_vazia:
        resultado[1] = "NAO"  # se_acertou
        resultado[2] = "NAO"  # explicacao_ta_boa
        resultado[3] = "NAO"  # sem_rastro_llm
        resultado[4] = "NAO"  # acordo_com_inep

    if gabarito_ausente:
        resultado[1] = "NAO"  # se_acertou
        resultado[4] = "NAO"  # acordo_com_inep

    if not anulada:
        resultado[5] = None  # anulada_tem_explicacao não se aplica
    elif resposta_vazia:
        resultado[5] = "NAO"

    return resultado


# ==================================================
# HELPERS: resultados existentes (resume) e salvamento incremental
# ==================================================

def carregar_resultados_existentes(caminho: str) -> pd.DataFrame:
    if not os.path.exists(caminho):
        return pd.DataFrame(columns=COLUNAS_RESULTADO)

    try:
        df = pd.read_csv(caminho, encoding="utf-8-sig")
    except Exception:
        return pd.DataFrame(columns=COLUNAS_RESULTADO)

    for coluna in COLUNAS_RESULTADO:
        if coluna not in df.columns:
            df[coluna] = None

    return df[COLUNAS_RESULTADO]


def questao_ja_concluida(df_resultados: pd.DataFrame, numero: int) -> bool:
    linhas = df_resultados[df_resultados["numero_da_questao"] == numero]

    if linhas.empty:
        return False

    linha = linhas.iloc[0]

    if pd.isna(linha["se_acertou"]):
        return False

    explicacao = str(linha.get("explicacao_final", ""))
    if explicacao.startswith("ERRO:"):
        return False

    return True


def salvar_resultado(
    df_resultados: pd.DataFrame, resultado: list, caminho: str
) -> pd.DataFrame:
    numero = resultado[0]

    # Remove qualquer linha anterior dessa mesma questão (ex.: uma
    # tentativa anterior que terminou em erro) antes de adicionar a
    # nova.
    df_resultados = df_resultados[
        df_resultados["numero_da_questao"] != numero
    ]

    nova_linha = pd.DataFrame([resultado], columns=COLUNAS_RESULTADO)
    df_resultados = pd.concat([df_resultados, nova_linha], ignore_index=True)

    df_resultados = df_resultados.sort_values("numero_da_questao")

    df_resultados.to_csv(caminho, index=False, encoding="utf-8-sig")

    return df_resultados


# ==================================================
# MAIN
# ==================================================

def main():

    # ==================================================
    # 1. LER AS DUAS PLANILHAS
    # ==================================================

    df_questoes = pd.read_csv(ARQUIVO_QUESTOES)
    df_gabarito = pd.read_csv(ARQUIVO_GABARITO)

    print(f"{len(df_questoes)} questões encontradas.")
    print(f"{len(df_gabarito)} gabaritos encontrados.\n")

    # ==================================================
    # 2. NORMALIZAR A COLUNA DE IDENTIFICAÇÃO
    # ==================================================

    df_questoes["numero_da_questao"] = (
        df_questoes["Questão "]
        .astype(str)
        .str.extract(r"(\d+)")
        .astype(int)
    )

    df_gabarito["numero_da_questao"] = (
        df_gabarito["Questão "]
        .astype(str)
        .str.extract(r"(\d+)")
        .astype(int)
    )

    # ==================================================
    # 3. JUNTAR AS DUAS PLANILHAS
    # ==================================================

    df = pd.merge(
        df_questoes,
        df_gabarito,
        on="numero_da_questao",
        how="left",
        suffixes=("_questao", "_gabarito")
    )

    print(f"{len(df)} questões após cruzamento.\n")

    # ==================================================
    # 4. CARREGAR RESULTADOS JÁ EXISTENTES (RESUME)
    # ==================================================

    df_resultados = carregar_resultados_existentes(ARQUIVO_SAIDA)

    if not df_resultados.empty:
        print(
            f"{len(df_resultados)} resultado(s) já salvo(s) em "
            f"{ARQUIVO_SAIDA}. Questões já concluídas serão puladas.\n"
        )

    # ==================================================
    # 5. PROCESSAR AS QUESTÕES
    # ==================================================

    for _, questao_bruta in df.iterrows():

        numero = int(questao_bruta["numero_da_questao"])

        if questao_ja_concluida(df_resultados, numero):
            print(f"Questão {numero} já concluída anteriormente. Pulando.\n")
            continue

        print(f"Processando questão {numero}...")

        try:

            # ------------------------------------------
            # Dados objetivos (controlados pelo Python)
            # ------------------------------------------

            dados = extrair_dados_questao(questao_bruta)

            if resposta_esta_vazia(dados["resposta_avaliada"]):
                print("  Atenção: nenhuma resposta avaliada foi encontrada "
                      "para esta questão.")

            # ------------------------------------------
            # Imagem
            # ------------------------------------------

            imagem = buscar_imagem(numero)

            if imagem:
                print(f"  Imagem encontrada: {imagem}")
            else:
                print("  Sem imagem.")

            # ------------------------------------------
            # Prompt
            # ------------------------------------------

            prompt = montar_prompt(dados)

            # ------------------------------------------
            # Mistral
            # ------------------------------------------

            print("  Enviando para Mistral...")

            resposta = avaliar(
                prompt=prompt,
                caminho_imagem=imagem
            )

            print("  Resposta recebida do Mistral.")

            # ------------------------------------------
            # Parser
            # ------------------------------------------

            resultado = processar_resposta(resposta)

            # Confere se o Mistral retornou a questão certa
            if resultado[0] != numero:
                raise ValueError(
                    f"O Mistral retornou a questão "
                    f"{resultado[0]}, mas era esperada a questão {numero}."
                )

            # Aplica as regras determinísticas (resposta ausente,
            # gabarito ausente, situação oficial) por cima do que o
            # modelo retornou, como camada final de proteção contra
            # alucinação.
            resultado = aplicar_regras_deterministicas(resultado, dados)

            print("  ✓ Questão processada.\n")

        except Exception as erro:

            print(f"  ✗ Erro na questão {numero}: {erro}\n")

            resultado = [
                numero,
                None,
                None,
                None,
                None,
                None,
                f"ERRO: {erro}"
            ]

        # ------------------------------------------
        # Salvamento incremental
        # ------------------------------------------

        df_resultados = salvar_resultado(df_resultados, resultado, ARQUIVO_SAIDA)

    # ==================================================
    # 6. FINALIZAÇÃO
    # ==================================================

    print("=" * 50)
    print("Processamento concluído!")
    print(f"Resultado salvo em: {ARQUIVO_SAIDA}")


if __name__ == "__main__":
    main()