import pandas as pd
from pathlib import Path

PASTA = Path("resultados")

ARQUIVO_PARTE1 = PASTA / "Judge_2017_Q09.xlsx"

ARQUIVO_PARTE2 = PASTA / "Judge_2014_parte2.xlsx"

ARQUIVO_SAIDA = PASTA / "Judge_2014_completo.xlsx"


def ler_aba(caminho, aba):
    return pd.read_excel(caminho, sheet_name=aba)



avaliacoes_1 = ler_aba(ARQUIVO_PARTE1, "Avaliacoes")
resumo_1 = ler_aba(ARQUIVO_PARTE1, "Resumo")

avaliacoes_2 = ler_aba(ARQUIVO_PARTE2, "Avaliacoes")
resumo_2 = ler_aba(ARQUIVO_PARTE2, "Resumo")


try:
    erros_1 = ler_aba(ARQUIVO_PARTE1, "Erros")
except Exception:
    erros_1 = pd.DataFrame()

try:
    erros_2 = ler_aba(ARQUIVO_PARTE2, "Erros")
except Exception:
    erros_2 = pd.DataFrame()



avaliacoes = pd.concat(
    [avaliacoes_1, avaliacoes_2],
    ignore_index=True
)

if "Questão" in avaliacoes.columns:
    avaliacoes = (
        avaliacoes
        .sort_values(by=["Questão"])
        .reset_index(drop=True)
    )



resumo = pd.concat(
    [resumo_1, resumo_2],
    ignore_index=True
)

if "Questão" in resumo.columns:
    resumo = (
        resumo
        .drop_duplicates(subset=["Questão"], keep="last")
        .sort_values(by=["Questão"])
        .reset_index(drop=True)
    )



erros = pd.concat(
    [erros_1, erros_2],
    ignore_index=True
)

if not erros.empty and "Questão" in erros.columns and "Questão" in resumo.columns:
    questoes_concluidas = set(resumo["Questão"].tolist())

    erros = erros[
        ~erros["Questão"].isin(questoes_concluidas)
    ].reset_index(drop=True)



questoes_esperadas = [5, 12, 14, 15, 16, 19, 22, 23, 27, 28, 30, 32, 35]

questoes_resumo = sorted(resumo["Questão"].tolist())

print()
print("==============================================")
print("MESCLAGEM JUDGE 2014")
print("==============================================")
print()

print("Questões esperadas:")
print(questoes_esperadas)
print()

print("Questões encontradas:")
print(questoes_resumo)
print()

print(f"Quantidade de linhas em Avaliacoes: {len(avaliacoes)}")
print(f"Quantidade de linhas em Resumo: {len(resumo)}")
print(f"Quantidade de linhas em Erros: {len(erros)}")
print()



with pd.ExcelWriter(ARQUIVO_SAIDA, engine="openpyxl") as writer:
    avaliacoes.to_excel(
        writer,
        sheet_name="Avaliacoes",
        index=False
    )

    resumo.to_excel(
        writer,
        sheet_name="Resumo",
        index=False
    )

    erros.to_excel(
        writer,
        sheet_name="Erros",
        index=False
    )


print("Arquivo criado:")
print(ARQUIVO_SAIDA)
print()



if questoes_resumo == questoes_esperadas:
    print("✓ As 13 questões de 2014 estão presentes.")
else:
    print("⚠ Atenção: a lista de questões não corresponde ao esperado.")

if len(avaliacoes) == 39:
    print("✓ Avaliacoes: 39 linhas, como esperado.")
else:
    print(f"⚠ Avaliacoes possui {len(avaliacoes)} linhas; o esperado era 39.")

if len(resumo) == 13:
    print("✓ Resumo: 13 linhas, como esperado.")
else:
    print(f"⚠ Resumo possui {len(resumo)} linhas; o esperado era 13.")

if len(erros) == 0:
    print("✓ Nenhum erro pendente.")
else:
    print("⚠ Ainda existem registros na aba Erros.")