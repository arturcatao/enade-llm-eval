import os
import json
import base64
import random
import time
from pathlib import Path
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from groq import Groq



ANO = 2014

ARQUIVO_EXCEL = "Enade_2014.xlsx"

PASTA_IMAGENS = Path("imagens") / str(ANO)
PASTA_RESULTADOS = Path("resultados")
PASTA_JSON = PASTA_RESULTADOS / "json_bruto"

ARQUIVO_SAIDA = PASTA_RESULTADOS / "Judge_2014_parte2.xlsx"
MODELO_JUDGE = "qwen/qwen3.8-27b"

QUESTOES_PROCESSAR = [27, 28, 30, 32, 35]

MAX_TENTATIVAS = 3

INTERVALO_ENTRE_QUESTOES = 65

MAX_IMAGENS_POR_QUESTAO = 3



load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError(
        "A variável GROQ_API_KEY não foi encontrada no arquivo .env."
    )

client = Groq(api_key=api_key)



PROMPT_JUDGE = """
Você atuará como avaliador independente da qualidade de três soluções
produzidas para uma questão objetiva de nível superior.

Você receberá:

1. o enunciado integral da questão;
2. três respostas anonimizadas, denominadas Resposta A, Resposta B
   e Resposta C;
3. quando necessário, uma ou mais imagens pertencentes originalmente
   à questão.

Sua função é avaliar a qualidade técnica, lógica e pedagógica das três
soluções.

IMPORTANTE:

- Não utilize pesquisa na internet, ferramentas de busca ou fontes externas.
- Baseie sua avaliação exclusivamente no enunciado, nas imagens fornecidas
  e nas três respostas apresentadas.
- Você NÃO receberá o gabarito oficial.
- Não tente identificar ou inferir qual modelo produziu cada resposta.
- Não considere concordância entre as respostas como evidência de correção.
- Avalie cada resposta de maneira independente.
- Não atribua pontuação maior a uma resposta apenas porque sua alternativa
  coincide com a escolhida pelas outras respostas.
- Determine a correção conceitual a partir do problema apresentado, e não
  da quantidade de respostas que concordam entre si.
- Não utilize informações de confiança, dificuldade, ambiguidade ou força
  dos distratores dos modelos respondentes. Essas informações não serão
  fornecidas.
- É permitido declarar empate técnico quando duas ou mais respostas
  apresentarem qualidade técnica e pedagógica essencialmente equivalente.
- Diferenças pequenas de pontuação não obrigam a considerar uma resposta
  qualitativamente superior.
- Não force a escolha de uma única resposta em caso de empate técnico
  justificável.

Avalie separadamente as Respostas A, B e C segundo os seguintes critérios,
atribuindo de 0 a 5 pontos em cada um:

1. CORREÇÃO CONCEITUAL

0 = conteúdo conceitualmente incorreto.
5 = conteúdo conceitualmente correto, preciso e sem erros relevantes.

2. COERÊNCIA LÓGICA

0 = raciocínio contraditório, inconsistente ou sem conexão lógica.
5 = raciocínio plenamente consistente e logicamente estruturado.

3. FUNDAMENTAÇÃO

0 = ausência de fundamentação ou justificativa inadequada.
5 = fundamentação completa, tecnicamente adequada e suficiente para
sustentar a resposta.

4. ANÁLISE DOS DISTRATORES

0 = alternativas incorretas não são analisadas ou são analisadas
incorretamente.
5 = as alternativas são analisadas adequadamente, identificando
corretamente por que a alternativa escolhida é superior aos distratores.

5. CLAREZA PEDAGÓGICA

0 = explicação confusa ou inadequada para fins educacionais.
5 = explicação clara, didática, objetiva e útil para estudantes.

6. ADERÊNCIA AO ENUNCIADO

0 = ignora, interpreta incorretamente ou distorce elementos relevantes
do enunciado.
5 = utiliza corretamente e de forma precisa as informações fornecidas
pela questão.

Para cada resposta:

- identifique a alternativa que ela efetivamente escolheu;
- atribua as seis notas solicitadas.

Após avaliar individualmente as três respostas:

- informe se existe empate técnico;
- se houver, informe quais respostas estão empatadas.

Sua saída deve ser estritamente estruturada e concisa.
Não escreva justificativas textuais adicionais no JSON.

Não utilize qualquer gabarito externo ou institucional.
"""



AVALIACAO_SCHEMA = {
    "type": "object",
    "properties": {
        "alternativa": {
            "type": "string",
            "enum": ["A", "B", "C", "D", "E"]
        },
        "correcao_conceitual": {
            "type": "integer",
            "minimum": 0,
            "maximum": 5
        },
        "coerencia_logica": {
            "type": "integer",
            "minimum": 0,
            "maximum": 5
        },
        "fundamentacao": {
            "type": "integer",
            "minimum": 0,
            "maximum": 5
        },
        "analise_distratores": {
            "type": "integer",
            "minimum": 0,
            "maximum": 5
        },
        "clareza_pedagogica": {
            "type": "integer",
            "minimum": 0,
            "maximum": 5
        },
        "aderencia_enunciado": {
            "type": "integer",
            "minimum": 0,
            "maximum": 5
        }
    },
    "required": [
        "alternativa",
        "correcao_conceitual",
        "coerencia_logica",
        "fundamentacao",
        "analise_distratores",
        "clareza_pedagogica",
        "aderencia_enunciado"
    ],
    "additionalProperties": False
}


SCHEMA_JUDGE = {
    "type": "object",
    "properties": {
        "resposta_a": AVALIACAO_SCHEMA,
        "resposta_b": AVALIACAO_SCHEMA,
        "resposta_c": AVALIACAO_SCHEMA,

        "empate_tecnico": {
            "type": "boolean"
        },

        "respostas_em_empate": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": ["A", "B", "C"]
            }
        }
    },

    "required": [
        "resposta_a",
        "resposta_b",
        "resposta_c",
        "empate_tecnico",
        "respostas_em_empate"
    ],

    "additionalProperties": False
}



def texto_seguro(valor):
    if pd.isna(valor):
        return ""

    return str(valor).strip()


def normalizar_alternativa(valor):
    valor = texto_seguro(valor).upper()

    if valor in ["A", "B", "C", "D", "E"]:
        return valor

    return valor


def montar_resposta(row):

    alternativa = texto_seguro(
        row["Alternativa"]
    )

    justificativa = texto_seguro(
        row["Justificativa da resposta"]
    )

    analise = texto_seguro(
        row["Análise das alternativas"]
    )

    return f"""
ALTERNATIVA ESCOLHIDA:
{alternativa}

JUSTIFICATIVA DA RESPOSTA:
{justificativa}

ANÁLISE DAS ALTERNATIVAS:
{analise}
""".strip()


def calcular_total(avaliacao):

    return (
        avaliacao["correcao_conceitual"]
        + avaliacao["coerencia_logica"]
        + avaliacao["fundamentacao"]
        + avaliacao["analise_distratores"]
        + avaliacao["clareza_pedagogica"]
        + avaliacao["aderencia_enunciado"]
    )


def localizar_imagens(numero_questao):

    prefixo = f"q{int(numero_questao):02d}"

    extensoes = [
        ".png",
        ".jpg",
        ".jpeg",
        ".webp"
    ]

    arquivos = []

    if not PASTA_IMAGENS.exists():
        return arquivos

    for arquivo in PASTA_IMAGENS.iterdir():

        if not arquivo.is_file():
            continue

        nome = arquivo.stem.lower()
        extensao = arquivo.suffix.lower()

        if (
            nome.startswith(prefixo)
            and extensao in extensoes
        ):
            arquivos.append(arquivo)

    return sorted(arquivos)


def mime_type(caminho):

    extensao = caminho.suffix.lower()

    if extensao == ".png":
        return "image/png"

    if extensao in [".jpg", ".jpeg"]:
        return "image/jpeg"

    if extensao == ".webp":
        return "image/webp"

    raise ValueError(
        f"Formato de imagem não suportado: {caminho}"
    )


def codificar_imagem(caminho):

    with open(caminho, "rb") as arquivo:

        return base64.b64encode(
            arquivo.read()
        ).decode("utf-8")


def salvar_json_bruto(numero, resultado):

    PASTA_JSON.mkdir(
        parents=True,
        exist_ok=True
    )

    caminho = (
        PASTA_JSON
        / f"q{int(numero):02d}_judge.json"
    )

    with open(
        caminho,
        "w",
        encoding="utf-8"
    ) as arquivo:

        json.dump(
            resultado,
            arquivo,
            ensure_ascii=False,
            indent=2
        )


def construir_conteudo_usuario(
    enunciado,
    respostas_anonimas,
    imagens
):

    texto = f"""
QUESTÃO:

{enunciado}

==================================================
RESPOSTA A
==================================================

{respostas_anonimas["A"]}

==================================================
RESPOSTA B
==================================================

{respostas_anonimas["B"]}

==================================================
RESPOSTA C
==================================================

{respostas_anonimas["C"]}
""".strip()

    conteudo = [
        {
            "type": "text",
            "text": texto
        }
    ]

    for imagem in imagens:

        imagem_base64 = codificar_imagem(
            imagem
        )

        tipo = mime_type(imagem)

        conteudo.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": (
                        f"data:{tipo};base64,"
                        f"{imagem_base64}"
                    )
                }
            }
        )

    return conteudo


def chamar_judge(conteudo_usuario):

    ultimo_erro = None

    for tentativa in range(
        1,
        MAX_TENTATIVAS + 1
    ):

        try:

            resposta = (
                client.chat.completions.create(
                    model=MODELO_JUDGE,

                    messages=[
                        {
                            "role": "system",
                            "content": PROMPT_JUDGE
                        },
                        {
                            "role": "user",
                            "content": conteudo_usuario
                        }
                    ],

                    reasoning_effort="medium",
                    reasoning_format="hidden",

                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": "avaliacao_judge",
                            "strict": True,
                            "schema": SCHEMA_JUDGE
                        }
                    },

                    temperature=1,
                    top_p=0.95,

                    max_completion_tokens=950,

                    stream=False
                )
            )

            texto = (
                resposta
                .choices[0]
                .message
                .content
            )

            return json.loads(texto)

        except Exception as erro:

            ultimo_erro = erro

            print(
                f"  Tentativa {tentativa} falhou:"
            )

            print(
                f"  {type(erro).__name__}: {erro}"
            )

            if tentativa < MAX_TENTATIVAS:

                espera = 2 ** tentativa

                print(
                    f"  Nova tentativa em "
                    f"{espera} segundos..."
                )

                time.sleep(espera)

    raise ultimo_erro


def determinar_melhor_base(
    df_questao,
    resultado_judge
):

    elegiveis = df_questao[
        df_questao["Elegível"] == "Sim"
    ].copy()

    if elegiveis.empty:

        return {
            "elegiveis": "Nenhuma",
            "melhor_base": "NENHUMA",
            "revisao_humana": "Sim",
            "motivo_revisao": (
                "Nenhuma das três respostas escolheu "
                "a alternativa do Gabarito INEP."
            )
        }

    codigos_elegiveis = set(
        elegiveis[
            "Resposta anônima"
        ].tolist()
    )

    respostas_empate_judge = set(
        resultado_judge[
            "respostas_em_empate"
        ]
    )

    empate_elegivel = (
        resultado_judge["empate_tecnico"]
        and len(
            codigos_elegiveis.intersection(
                respostas_empate_judge
            )
        ) >= 2
    )

    if empate_elegivel:

        empatadas = sorted(
            codigos_elegiveis.intersection(
                respostas_empate_judge
            )
        )

        melhor_base = (
            "EMPATE TÉCNICO: "
            + "+".join(empatadas)
        )

    else:

        maior_total = (
            elegiveis["Total"].max()
        )

        melhores = elegiveis[
            elegiveis["Total"]
            == maior_total
        ]

        if len(melhores) == 1:

            melhor_base = (
                melhores.iloc[0][
                    "Resposta anônima"
                ]
            )

        else:

            codigos = sorted(
                melhores[
                    "Resposta anônima"
                ].tolist()
            )

            melhor_base = (
                "EMPATE POR PONTUAÇÃO: "
                + "+".join(codigos)
            )


    divergencia_extracao = (
        df_questao[
            "Alternativa original"
        ]
        !=
        df_questao[
            "Alternativa identificada pelo Judge"
        ]
    ).any()

    if divergencia_extracao:

        revisao = "Sim"

        motivo = (
            "O Judge identificou pelo menos uma "
            "alternativa diferente da registrada "
            "originalmente na planilha."
        )

    else:

        revisao = "Não"

        motivo = ""

    return {
        "elegiveis": ", ".join(
            sorted(codigos_elegiveis)
        ),
        "melhor_base": melhor_base,
        "revisao_humana": revisao,
        "motivo_revisao": motivo
    }


def salvar_excel(
    linhas_avaliacoes,
    linhas_resumo,
    linhas_erros
):

    PASTA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True
    )

    df_avaliacoes = pd.DataFrame(
        linhas_avaliacoes
    )

    df_resumo = pd.DataFrame(
        linhas_resumo
    )

    df_erros = pd.DataFrame(
        linhas_erros
    )

    with pd.ExcelWriter(
        ARQUIVO_SAIDA,
        engine="openpyxl"
    ) as writer:

        df_avaliacoes.to_excel(
            writer,
            sheet_name="Avaliacoes",
            index=False
        )

        df_resumo.to_excel(
            writer,
            sheet_name="Resumo",
            index=False
        )

        df_erros.to_excel(
            writer,
            sheet_name="Erros",
            index=False
        )



print()
print(
    "=============================================="
)

print(
    f"ENADE JUDGE - {ANO}"
)

print(
    "=============================================="
)

print()

print(
    f"Modelo Judge: {MODELO_JUDGE}"
)

print(
    "Gabarito INEP: oculto durante a avaliação"
)

print()



print(
    f"Carregando {ARQUIVO_EXCEL}..."
)

questoes = pd.read_excel(
    ARQUIVO_EXCEL,
    sheet_name="Questões"
)

respostas = pd.read_excel(
    ARQUIVO_EXCEL,
    sheet_name="Respostas LLM"
)

gabaritos = pd.read_excel(
    ARQUIVO_EXCEL,
    sheet_name="Gabarito_INEP"
)


questoes.columns = (
    questoes.columns
    .astype(str)
    .str.strip()
)

respostas.columns = (
    respostas.columns
    .astype(str)
    .str.strip()
)

gabaritos.columns = (
    gabaritos.columns
    .astype(str)
    .str.strip()
)


print(
    "Planilha carregada."
)


def normalizar_numero_questao(valor):
    texto = str(valor).strip()

    texto = (
        texto
        .replace("Questão", "")
        .replace("questão", "")
        .replace("QUESTÃO", "")
        .strip()
    )

    return int(texto)


questoes["Questão"] = questoes["Questão"].apply(
    normalizar_numero_questao
)

respostas["Questão"] = respostas["Questão"].apply(
    normalizar_numero_questao
)

gabaritos["Questão"] = gabaritos["Questão"].apply(
    normalizar_numero_questao
)

colunas_questoes = [
    "Questão",
    "Enunciado",
    "Possui figura?"
]

colunas_respostas = [
    "Questão",
    "LLM",
    "Modelo",
    "Alternativa",
    "Justificativa da resposta",
    "Análise das alternativas"
]

colunas_gabarito = [
    "Questão",
    "Gabarito INEP"
]


for coluna in colunas_questoes:

    if coluna not in questoes.columns:

        raise KeyError(
            f"Coluna ausente em Questões: "
            f"{coluna}"
        )


for coluna in colunas_respostas:

    if coluna not in respostas.columns:

        raise KeyError(
            f"Coluna ausente em Respostas LLM: "
            f"{coluna}"
        )


for coluna in colunas_gabarito:

    if coluna not in gabaritos.columns:

        raise KeyError(
            f"Coluna ausente em Gabarito_INEP: "
            f"{coluna}"
        )



numeros = (
    questoes["Questão"]
    .dropna()
    .astype(int)
    .tolist()
)


if QUESTOES_PROCESSAR is not None:

    numeros = [
        numero
        for numero in numeros
        if numero in QUESTOES_PROCESSAR
    ]


print(
    f"Questões a processar: {len(numeros)}"
)

print(
    numeros
)

print()



linhas_avaliacoes = []
linhas_resumo = []
linhas_erros = []



total_questoes = len(numeros)


for posicao, numero in enumerate(
    numeros,
    start=1
):

    print(
        "----------------------------------------------"
    )

    print(
        f"[{posicao}/{total_questoes}] "
        f"Questão {numero}"
    )

    try:


        linha_q = questoes[
            questoes["Questão"]
            .astype("Int64")
            == numero
        ]

        if linha_q.empty:

            raise ValueError(
                "Questão não encontrada."
            )

        enunciado = texto_seguro(
            linha_q.iloc[0]["Enunciado"]
        )

        possui_figura = (
            texto_seguro(
                linha_q.iloc[0][
                    "Possui figura?"
                ]
            ).lower()
            == "sim"
        )



        respostas_q = respostas[
            respostas["Questão"]
            .astype("Int64")
            == numero
        ].copy()

        if len(respostas_q) != 3:

            raise ValueError(
                f"Foram encontradas "
                f"{len(respostas_q)} respostas; "
                f"eram esperadas 3."
            )



        imagens = localizar_imagens(
            numero
        )

        if possui_figura and not imagens:

            raise FileNotFoundError(
                f"A questão está marcada como "
                f"'Possui figura? = Sim', mas "
                f"nenhuma imagem q{numero:02d}* "
                f"foi encontrada em "
                f"{PASTA_IMAGENS}."
            )

        if len(imagens) > MAX_IMAGENS_POR_QUESTAO:

            raise ValueError(
                f"A questão possui "
                f"{len(imagens)} imagens, mas o "
                f"modelo aceita no máximo "
                f"{MAX_IMAGENS_POR_QUESTAO}."
            )

        if imagens:

            print(
                "  Imagens:"
            )

            for imagem in imagens:

                print(
                    f"    - {imagem.name}"
                )

        else:

            print(
                "  Sem imagem."
            )



        random.seed(
            ANO * 100
            + numero
        )

        indices = list(
            respostas_q.index
        )

        random.shuffle(
            indices
        )

        codigos = [
            "A",
            "B",
            "C"
        ]

        mapa_anonimo = {}

        respostas_anonimas = {}


        for codigo, indice in zip(
            codigos,
            indices
        ):

            row = respostas.loc[
                indice
            ]

            mapa_anonimo[codigo] = {
                "llm": texto_seguro(
                    row["LLM"]
                ),
                "modelo": texto_seguro(
                    row["Modelo"]
                ),
                "alternativa_original":
                    normalizar_alternativa(
                        row["Alternativa"]
                    )
            }

            respostas_anonimas[
                codigo
            ] = montar_resposta(
                row
            )


        print(
            "  Respostas anonimizadas."
        )



        conteudo_usuario = (
            construir_conteudo_usuario(
                enunciado,
                respostas_anonimas,
                imagens
            )
        )



        print(
            "  Enviando ao Judge..."
        )

        resultado_judge = (
            chamar_judge(
                conteudo_usuario
            )
        )

        print(
            "  Avaliação recebida."
        )



        salvar_json_bruto(
            numero,
            resultado_judge
        )



        linha_gabarito = gabaritos[
            gabaritos["Questão"]
            .astype("Int64")
            == numero
        ]

        if linha_gabarito.empty:

            raise ValueError(
                "Gabarito INEP não encontrado."
            )

        gabarito_inep = (
            normalizar_alternativa(
                linha_gabarito.iloc[0][
                    "Gabarito INEP"
                ]
            )
        )



        inicio_resultados = len(
            linhas_avaliacoes
        )

        for codigo in [
            "A",
            "B",
            "C"
        ]:

            chave = (
                f"resposta_"
                f"{codigo.lower()}"
            )

            avaliacao = (
                resultado_judge[
                    chave
                ]
            )

            total = calcular_total(
                avaliacao
            )

            alternativa_judge = (
                normalizar_alternativa(
                    avaliacao[
                        "alternativa"
                    ]
                )
            )

            alternativa_original = (
                mapa_anonimo[codigo][
                    "alternativa_original"
                ]
            )


            elegivel = (
                alternativa_original
                == gabarito_inep
            )


            confere_extracao = (
                alternativa_original
                == alternativa_judge
            )


            linhas_avaliacoes.append(
                {
                    "Ano": ANO,

                    "Questão":
                        numero,

                    "Resposta anônima":
                        codigo,

                    "LLM real":
                        mapa_anonimo[
                            codigo
                        ]["llm"],

                    "Modelo real":
                        mapa_anonimo[
                            codigo
                        ]["modelo"],

                    "Alternativa original":
                        alternativa_original,

                    "Alternativa identificada pelo Judge":
                        alternativa_judge,

                    "Judge identificou alternativa corretamente?":
                        (
                            "Sim"
                            if confere_extracao
                            else "Não"
                        ),

                    "Gabarito INEP":
                        gabarito_inep,

                    "Elegível":
                        (
                            "Sim"
                            if elegivel
                            else "Não"
                        ),

                    "Correção conceitual":
                        avaliacao[
                            "correcao_conceitual"
                        ],

                    "Coerência lógica":
                        avaliacao[
                            "coerencia_logica"
                        ],

                    "Fundamentação":
                        avaliacao[
                            "fundamentacao"
                        ],

                    "Análise dos distratores":
                        avaliacao[
                            "analise_distratores"
                        ],

                    "Clareza pedagógica":
                        avaliacao[
                            "clareza_pedagogica"
                        ],

                    "Aderência ao enunciado":
                        avaliacao[
                            "aderencia_enunciado"
                        ],

                    "Total":
                        total,

                    "Modelo Judge":
                        MODELO_JUDGE
                }
            )



        df_questao = pd.DataFrame(
            linhas_avaliacoes[
                inicio_resultados:
            ]
        )

        selecao = (
            determinar_melhor_base(
                df_questao,
                resultado_judge
            )
        )


        linhas_resumo.append(
            {
                "Ano":
                    ANO,

                "Questão":
                    numero,

                "Gabarito INEP":
                    gabarito_inep,

                "Respostas elegíveis":
                    selecao[
                        "elegiveis"
                    ],

                "Melhor resposta-base":
                    selecao[
                        "melhor_base"
                    ],

                "Empate técnico declarado pelo Judge":
                    (
                        "Sim"
                        if resultado_judge[
                            "empate_tecnico"
                        ]
                        else "Não"
                    ),

                "Respostas em empate segundo o Judge":
                    ", ".join(
                        resultado_judge[
                            "respostas_em_empate"
                        ]
                    ),

                "Revisão humana recomendada":
                    selecao[
                        "revisao_humana"
                    ],

                "Motivo da revisão humana":
                    selecao[
                        "motivo_revisao"
                    ],

                "Número de imagens":
                    len(imagens),

                "Arquivos de imagem":
                    ", ".join(
                        [
                            imagem.name
                            for imagem
                            in imagens
                        ]
                    ),

                "Modelo Judge":
                    MODELO_JUDGE,

                "Data da avaliação":
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
            }
        )



        print(
            f"  Gabarito consultado após "
            f"a avaliação: {gabarito_inep}"
        )

        print(
            f"  Elegíveis: "
            f"{selecao['elegiveis']}"
        )

        print(
            f"  Melhor base: "
            f"{selecao['melhor_base']}"
        )

        print(
            "  ✓ Questão concluída."
        )


    except Exception as erro:

        print(
            "  ✗ ERRO NA QUESTÃO:"
        )

        print(
            f"    {type(erro).__name__}: "
            f"{erro}"
        )

        linhas_erros.append(
            {
                "Ano":
                    ANO,

                "Questão":
                    numero,

                "Tipo do erro":
                    type(erro).__name__,

                "Mensagem":
                    str(erro),

                "Data":
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
            }
        )



    salvar_excel(
        linhas_avaliacoes,
        linhas_resumo,
        linhas_erros
    )

    print(
        "  Checkpoint salvo."
    )

    print()


    if (
        posicao
        < total_questoes
    ):
        time.sleep(
            INTERVALO_ENTRE_QUESTOES
        )



print()
print(
    "=============================================="
)

print(
    "PROCESSAMENTO FINALIZADO"
)

print(
    "=============================================="
)

print()

print(
    f"Questões solicitadas: "
    f"{total_questoes}"
)

print(
    f"Questões concluídas: "
    f"{len(linhas_resumo)}"
)

print(
    f"Questões com erro: "
    f"{len(linhas_erros)}"
)

print()

print(
    f"Resultado salvo em:"
)

print(
    ARQUIVO_SAIDA
)

print()

print(
    f"JSONs individuais salvos em:"
)

print(
    PASTA_JSON
)

print()