import pandas as pd
from pathlib import Path

PASTA_RESULTADOS = Path("resultados")

ARQUIVO_GERAL = PASTA_RESULTADOS / "Judge_2017.xlsx"
ARQUIVO_Q09 = PASTA_RESULTADOS / "Judge_2017_Q09.xlsx"
ARQUIVO_SAIDA = PASTA_RESULTADOS / "Judge_2017_completo.xlsx"

avaliacoes_geral = pd.read_excel(
    ARQUIVO_GERAL,
    sheet_name="Avaliacoes"
)

resumo_geral = pd.read_excel(
    ARQUIVO_GERAL,
    sheet_name="Resumo"
)

erros_geral = pd.read_excel(
    ARQUIVO_GERAL,
    sheet_name="Erros"
)

avaliacoes_q09 = pd.read_excel(
    ARQUIVO_Q09,
    sheet_name="Avaliacoes"
)

resumo_q09 = pd.read_excel(
    ARQUIVO_Q09,
    sheet_name="Resumo"
)

erros_q09 = pd.read_excel(
    ARQUIVO_Q09,
    sheet_name="Erros"
)

avaliacoes_geral = avaliacoes_geral[
    avaliacoes_geral["Questão"] != 9
]

resumo_geral = resumo_geral[
    resumo_geral["Questão"] != 9
]

erros_geral = erros_geral[
    erros_geral["Questão"] != 9
]

avaliacoes_final = pd.concat(
    [avaliacoes_geral, avaliacoes_q09],
    ignore_index=True
)

resumo_final = pd.concat(
    [resumo_geral, resumo_q09],
    ignore_index=True
)

erros_final = pd.concat(
    [erros_geral, erros_q09],
    ignore_index=True
)

avaliacoes_final = avaliacoes_final.sort_values(
    by=["Questão", "Resposta anônima"]
)

resumo_final = resumo_final.sort_values(
    by=["Questão"]
)

if not erros_final.empty:
    erros_final = erros_final.sort_values(
        by=["Questão"]
    )

with pd.ExcelWriter(
    ARQUIVO_SAIDA,
    engine="openpyxl"
) as writer:

    avaliacoes_final.to_excel(
        writer,
        sheet_name="Avaliacoes",
        index=False
    )

    resumo_final.to_excel(
        writer,
        sheet_name="Resumo",
        index=False
    )

    erros_final.to_excel(
        writer,
        sheet_name="Erros",
        index=False
    )

print()
print("Arquivo completo criado com sucesso:")
print(ARQUIVO_SAIDA)

print()
print(
    f"Avaliações: {len(avaliacoes_final)} linhas"
)

print(
    f"Resumo: {len(resumo_final)} questões"
)

print(
    f"Erros restantes: {len(erros_final)}"
)