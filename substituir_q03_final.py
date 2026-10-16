import pandas as pd
from pathlib import Path

PASTA = Path("resultados")

ARQUIVO_GERAL = PASTA / "Gabarito_Final_2017.xlsx"
ARQUIVO_Q03 = PASTA / "Gabarito_Final_2017_Q03.xlsx"
ARQUIVO_SAIDA = PASTA / "Gabarito_Final_2017_CORRIGIDO.xlsx"


geral = pd.read_excel(
    ARQUIVO_GERAL,
    sheet_name="Gabarito Final"
)

erros_geral = pd.read_excel(
    ARQUIVO_GERAL,
    sheet_name="Erros"
)


q03 = pd.read_excel(
    ARQUIVO_Q03,
    sheet_name="Gabarito Final"
)


geral = geral[
    geral["Questão"] != 3
]


final = pd.concat(
    [geral, q03],
    ignore_index=True
)


final = final.sort_values(
    by="Questão"
).reset_index(drop=True)


if not erros_geral.empty and "Questão" in erros_geral.columns:
    erros_geral = erros_geral[
        erros_geral["Questão"] != 3
    ]


with pd.ExcelWriter(
    ARQUIVO_SAIDA,
    engine="openpyxl"
) as writer:

    final.to_excel(
        writer,
        sheet_name="Gabarito Final",
        index=False
    )

    erros_geral.to_excel(
        writer,
        sheet_name="Erros",
        index=False
    )


print()
print("Arquivo corrigido criado:")
print(ARQUIVO_SAIDA)

print()
print(
    f"Quantidade de questões: {len(final)}"
)

print(
    "Questão 3 presente:",
    3 in final["Questão"].tolist()
)