import pandas as pd

from prompt import montar_prompt
from images import buscar_imagem
from mistral import avaliar
from parser import processar_resposta


ARQUIVO_ENTRADA = "data/questoes.csv"
ARQUIVO_SAIDA = "data/resultados.csv"


def main():
    # 1. Lê o CSV original
    df = pd.read_csv(ARQUIVO_ENTRADA)

    resultados = []

    print(f"{len(df)} questões encontradas.\n")

    # 2. Processa cada questão
    for indice, questao in df.iterrows():

        numero = int(questao["numero_da_questao"])

        print(f"Processando questão {numero}...")

        try:
            # 3. Procura imagem da questão
            imagem = buscar_imagem(numero)

            if imagem:
                print(f"  Imagem encontrada: {imagem}")
            else:
                print("  Sem imagem.")

            # 4. Monta o prompt
            prompt = montar_prompt(questao)

            # 5. Envia para o Mistral
            resposta = avaliar(
                prompt=prompt,
                caminho_imagem=imagem
            )

            print(f"  Resposta recebida: {resposta}")

            # 6. Faz o parsing e validação
            resultado = processar_resposta(resposta)

            if resultado[0] != numero:
                raise ValueError(
                    f"O Mistral retornou a questão {resultado[0]}, "
                    f"mas a questão processada era {numero}."
                )

            # 7. Adiciona o resultado ao DataFrame
            resultados.append(resultado)

            print("  ✓ Questão processada.\n")

        except Exception as erro:
            print(f"  ✗ Erro na questão {numero}: {erro}\n")

            # Mantém um registro do erro
            resultados.append([
                numero,
                None,
                None,
                None,
                None,
                None,
                f"ERRO: {erro}"
            ])

    # 8. Converte os resultados para DataFrame
    colunas_resultado = [
        "numero_resultado",
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

    # 9. Junta os dados originais com os resultados
    df_final = pd.concat(
        [
            df.reset_index(drop=True),
            df_resultados
        ],
        axis=1
    )

    # 10. Salva o novo CSV
    df_final.to_csv(
        ARQUIVO_SAIDA,
        index=False,
        encoding="utf-8-sig"
    )

    print("=" * 50)
    print("Processamento concluído!")
    print(f"Resultado salvo em: {ARQUIVO_SAIDA}")


if __name__ == "__main__":
    main()