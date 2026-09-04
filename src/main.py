import pandas as pd

from prompt import montar_prompt
from images import buscar_imagem
from mistral import avaliar
from parser import processar_resposta


ARQUIVO_QUESTOES = "../data/2021/Enade2021-Questões.csv"
ARQUIVO_GABARITO = "../data/2021/Enade2021-GabaritoFinal.csv"
ARQUIVO_SAIDA = "../data/resultados.csv"


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
    # 4. PROCESSAR AS QUESTÕES
    # ==================================================

    resultados = []

    # TESTE:
    # Processa somente a primeira questão.
    #
    # Quando estiver tudo funcionando, troque:
    #     df.head(1)
    #
    # por:
    #     df

    for _, questao in df.iterrows():

        numero = int(questao["numero_da_questao"])

        print(f"Processando questão {numero}...")

        try:

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

            prompt = montar_prompt(questao)

            # ------------------------------------------
            # Mistral
            # ------------------------------------------

            print("  Enviando para Mistral...")

            resposta = avaliar(
                prompt=prompt,
                caminho_imagem=imagem
            )

            print("TIPO DA RESPOSTA:", type(resposta))
            print("REPR DA RESPOSTA:", repr(resposta))

            print("  Resposta recebida do Mistral!")

            print("\n  Resposta recebida:")
            print(resposta)
            print()

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

            resultados.append(resultado)

            print("  ✓ Questão processada.\n")

        except Exception as erro:

            print(f"  ✗ Erro na questão {numero}: {erro}\n")

            resultados.append([
                numero,
                None,
                None,
                None,
                None,
                None,
                f"ERRO: {erro}"
            ])

    # ==================================================
    # 5. TRANSFORMAR RESULTADOS EM DATAFRAME
    # ==================================================

    colunas_resultado = [
        "numero_da_questao",
        "se_acertou",
        "explicacao_ta_boa",
        "sem_rastro_llm",
        "acordo_com_inep",
        "anulada_tem_explicacao",
        "explicacao_final"
    ]

    df_resultados = pd.DataFrame(
        resultados,
        columns=colunas_resultado
    )

    # ==================================================
    # 6. SALVAR SOMENTE OS RESULTADOS
    # ==================================================

    df_resultados.to_csv(
        ARQUIVO_SAIDA,
        index=False,
        encoding="utf-8-sig"
    )

    # ==================================================
    # 7. FINALIZAÇÃO
    # ==================================================

    print("=" * 50)
    print("Processamento concluído!")
    print(f"Resultado salvo em: {ARQUIVO_SAIDA}")


if __name__ == "__main__":
    main()