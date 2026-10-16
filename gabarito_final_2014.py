import os
import json
import base64
import time
from pathlib import Path
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from groq import Groq



ANO = 2014

ARQUIVO_DADOS = Path("Enade_2014.xlsx")

ARQUIVO_JUDGE = Path("resultados") / "Judge_2014_completo.xlsx"

PASTA_IMAGENS = Path("imagens") / "2014"

PASTA_RESULTADOS = Path("resultados")

PASTA_JSON_FINAL = PASTA_RESULTADOS / "json_final_2014"

ARQUIVO_SAIDA = PASTA_RESULTADOS / "Gabarito_Final_2014.xlsx"

MODELO_FINALIZADOR = "openai/gpt-oss-120b"

MODELO_VISAO = "qwen/qwen3.8-27b"


QUESTOES_PROCESSAR = [5, 12, 14, 15, 16, 19, 22, 23, 27, 28, 30, 32, 35]


INTERVALO_ENTRE_QUESTOES = 20


MAX_TENTATIVAS = 3



load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError(
        "GROQ_API_KEY não encontrada no arquivo .env."
    )

client = Groq(api_key=api_key)



PROMPT_FINALIZADOR = """
Você atuará como professor especialista na resolução de questões
objetivas de nível superior do ENADE de Ciência da Computação.

Sua tarefa é produzir um GABARITO COMENTADO FINAL padronizado.

Você receberá:

1. número da questão;
2. enunciado integral;
3. alternativa correta oficial;
4. eventualmente uma descrição técnica de figuras, tabelas,
   diagramas ou elementos visuais da questão;
5. uma ou mais respostas-base previamente selecionadas por um
   processo independente de avaliação.

IMPORTANTE:

A alternativa correta fornecida nos dados da questão é uma
restrição objetiva desta tarefa.

O texto final deve obrigatoriamente concluir pela alternativa
informada como correta.

As respostas-base são apenas material técnico auxiliar.

Elas podem:

- conter explicações úteis;
- conter abordagens diferentes;
- possuir níveis diferentes de detalhamento;
- apresentar omissões;
- eventualmente conter algum erro secundário.

Portanto:

- não copie mecanicamente a resposta-base;
- verifique internamente sua coerência;
- preserve os raciocínios tecnicamente corretos;
- corrija erros secundários;
- complete explicações insuficientes;
- elimine redundâncias;
- sintetize respostas-base quando houver mais de uma;
- produza uma resolução final independente e uniforme.

Se nenhuma resposta-base for fornecida, resolva a questão
diretamente a partir do enunciado, da alternativa correta
informada e dos elementos visuais fornecidos.

============================================================
PADRÃO OBRIGATÓRIO DA RESOLUÇÃO
============================================================

A resposta final deve começar EXATAMENTE neste formato:

QUESTÃO [número] — Alternativa [letra]

Em seguida:

Comentário geral

Explique o tema da questão e desenvolva o raciocínio necessário
para determinar a resposta correta.

Não seja excessivamente breve.

A explicação deve permitir que um estudante compreenda como
resolver a questão.

Quando houver cálculos:

- apresente as etapas relevantes;
- explique as operações;
- apresente o resultado;
- relacione-o à alternativa correta.

Quando houver código:

- explique o comportamento relevante do programa;
- acompanhe as estruturas, variáveis ou operações necessárias;
- explique como isso conduz à resposta.

Quando houver afirmações I, II, III etc.:

adicione a seção:

Análise das afirmações

e analise cada afirmação individualmente antes de concluir qual
combinação corresponde à alternativa correta.

Quando houver figura, tabela, gráfico, circuito, árvore,
diagrama ou outro elemento visual:

- incorpore sua interpretação ao raciocínio;
- não mencione que recebeu uma descrição da imagem;
- trate o conteúdo visual como parte normal da própria questão.

Depois, apresente:

Análise das alternativas

A) Explique tecnicamente por que está correta ou incorreta.

B) Explique tecnicamente por que está correta ou incorreta.

C) Explique tecnicamente por que está correta ou incorreta.

D) Explique tecnicamente por que está correta ou incorreta.

E) Explique tecnicamente por que está correta ou incorreta.

============================================================
REGRAS DE QUALIDADE
============================================================

- A resolução deve ser autocontida.
- A linguagem deve ser natural, acadêmica e didática.
- Escreva como um professor explicando a questão para um aluno.
- Não seja superficial.
- Não apenas diga que uma alternativa está incorreta:
  explique por que está incorreta.
- Quando uma alternativa for parcialmente plausível, explique
  o ponto específico que a torna incorreta.
- Não invente informações desnecessárias.
- Não acrescente conteúdos que não contribuam para a resolução.
- Evite repetições.
- Evite frases genéricas.
- Não faça comentários sobre a qualidade das respostas-base.
- Não compare os modelos.
- Não identifique a origem de nenhuma resposta-base.

============================================================
PROIBIÇÕES NO TEXTO FINAL
============================================================

O texto final NÃO deve mencionar:

- INEP;
- gabarito oficial;
- Judge;
- Groq;
- ChatGPT;
- Gemini;
- Claude;
- LLM;
- inteligência artificial;
- modelo de linguagem;
- resposta-base;
- processo de seleção;
- pontuação;
- confiança;
- dificuldade;
- ambiguidade;
- força dos distratores;
- critérios de avaliação;
- experimento;
- metodologia.

O texto deve parecer simplesmente um gabarito comentado
produzido por um professor especialista.

============================================================
FORMATO DA RESPOSTA
============================================================

Retorne SOMENTE o texto completo do gabarito comentado.

Não use JSON.

Não coloque ```.

Não escreva qualquer observação antes ou depois da resolução.
"""



PROMPT_VISAO = """
Analise cuidadosamente o elemento visual pertencente a uma
questão objetiva do ENADE.

Sua função NÃO é elaborar o gabarito comentado final.

Sua função é apenas produzir uma descrição técnica, objetiva e
precisa das informações visuais necessárias para resolver a
questão.

A descrição poderá ser fornecida posteriormente a outro modelo
que receberá o enunciado completo.

Portanto:

- transcreva textos relevantes;
- identifique valores numéricos;
- identifique relações espaciais ou lógicas;
- descreva tabelas;
- descreva gráficos;
- descreva diagramas;
- descreva circuitos;
- descreva árvores;
- descreva códigos mostrados graficamente;
- descreva alternativas gráficas quando existirem.

Não faça comentários sobre qualidade de imagem.

Não mencione que você é um modelo.

Não invente elementos não visíveis.

Não produza uma resposta excessivamente longa.

Se o visual permitir determinar algum resultado técnico
necessário para resolver a questão, descreva também esse
resultado de forma objetiva.

Retorne somente a descrição técnica.
"""



def texto_seguro(valor):

    if pd.isna(valor):
        return ""

    return str(valor).strip()


def normalizar_alternativa(valor):

    texto = texto_seguro(valor).upper()

    if texto in ["A", "B", "C", "D", "E"]:
        return texto

    return texto


def normalizar_colunas(df):

    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
    )

    return df


def localizar_imagens(numero):

    if not PASTA_IMAGENS.exists():
        return []

    prefixo = f"q{int(numero):02d}"

    extensoes = {
        ".png",
        ".jpg",
        ".jpeg",
        ".webp"
    }

    arquivos = []

    for caminho in PASTA_IMAGENS.iterdir():

        if not caminho.is_file():
            continue

        if (
            caminho.stem.lower().startswith(prefixo)
            and caminho.suffix.lower() in extensoes
        ):

            arquivos.append(caminho)

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
        f"Formato não suportado: {caminho}"
    )


def imagem_base64(caminho):

    with open(caminho, "rb") as arquivo:

        return base64.b64encode(
            arquivo.read()
        ).decode("utf-8")



def descrever_imagens(
    numero,
    enunciado,
    imagens
):

    if not imagens:
        return ""

    print(
        "  Interpretando elemento(s) visual(is)..."
    )

    conteudo = [
        {
            "type": "text",
            "text": (
                f"{PROMPT_VISAO}\n\n"
                f"Número da questão: {numero}\n\n"
                f"Enunciado:\n{enunciado}"
            )
        }
    ]


    for imagem in imagens:

        encoded = imagem_base64(
            imagem
        )

        tipo = mime_type(
            imagem
        )

        conteudo.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": (
                        f"data:{tipo};base64,"
                        f"{encoded}"
                    )
                }
            }
        )


    ultimo_erro = None


    for tentativa in range(
        1,
        MAX_TENTATIVAS + 1
    ):

        try:

            resposta = (
                client.chat.completions.create(
                    model=MODELO_VISAO,

                    messages=[
                        {
                            "role": "user",
                            "content": conteudo
                        }
                    ],

                    reasoning_effort="medium",
                    reasoning_format="hidden",

                    temperature=1,
                    top_p=0.95,

                    max_completion_tokens=700,

                    stream=False
                )
            )


            descricao = (
                resposta
                .choices[0]
                .message
                .content
                .strip()
            )

            print(
                "  Descrição visual concluída."
            )

            return descricao


        except Exception as erro:

            ultimo_erro = erro

            print(
                f"  Tentativa visual "
                f"{tentativa} falhou:"
            )

            print(
                f"  {type(erro).__name__}: "
                f"{erro}"
            )

            if tentativa < MAX_TENTATIVAS:

                espera = (
                    15 * tentativa
                )

                print(
                    f"  Aguardando "
                    f"{espera}s..."
                )

                time.sleep(
                    espera
                )


    raise ultimo_erro



def codigos_da_base(
    linha_resumo,
    avaliacoes_q
):

    melhor = texto_seguro(
        linha_resumo[
            "Melhor resposta-base"
        ]
    )


    if (
        not melhor
        or melhor.upper()
        == "NENHUMA"
    ):
        return []


    if melhor in [
        "A",
        "B",
        "C"
    ]:
        return [
            melhor
        ]



    if ":" in melhor:

        parte = (
            melhor
            .split(":", 1)[1]
            .strip()
        )

        codigos = [
            codigo.strip()
            for codigo
            in parte.split("+")
        ]

        codigos = [
            codigo
            for codigo
            in codigos
            if codigo in [
                "A",
                "B",
                "C"
            ]
        ]

        if codigos:
            return codigos



    elegiveis = avaliacoes_q[
        avaliacoes_q["Elegível"]
        == "Sim"
    ]

    if elegiveis.empty:
        return []


    max_total = (
        elegiveis["Total"].max()
    )

    melhores = elegiveis[
        elegiveis["Total"]
        == max_total
    ]


    return (
        melhores[
            "Resposta anônima"
        ]
        .astype(str)
        .tolist()
    )



def recuperar_respostas_base(
    numero,
    codigos,
    avaliacoes_q,
    respostas_originais
):

    bases = []


    for codigo in codigos:

        linha_judge = avaliacoes_q[
            avaliacoes_q[
                "Resposta anônima"
            ].astype(str)
            == codigo
        ]

        if linha_judge.empty:
            continue


        llm_real = texto_seguro(
            linha_judge.iloc[0][
                "LLM real"
            ]
        )


        linha_original = (
            respostas_originais[
                (
                    respostas_originais[
                        "Questão"
                    ].astype("Int64")
                    == numero
                )
                &
                (
                    respostas_originais[
                        "LLM"
                    ].astype(str)
                    .str.strip()
                    == llm_real
                )
            ]
        )


        if linha_original.empty:

            print(
                f"  Aviso: resposta original "
                f"de {llm_real} não encontrada."
            )

            continue


        row = linha_original.iloc[0]


        alternativa = texto_seguro(
            row["Alternativa"]
        )

        justificativa = texto_seguro(
            row[
                "Justificativa da resposta"
            ]
        )

        analise = texto_seguro(
            row[
                "Análise das alternativas"
            ]
        )


        texto = f"""
ALTERNATIVA ESCOLHIDA:
{alternativa}

JUSTIFICATIVA:
{justificativa}

ANÁLISE DAS ALTERNATIVAS:
{analise}
""".strip()


        bases.append(
            {
                "codigo": codigo,
                "llm": llm_real,
                "texto": texto
            }
        )


    return bases



def montar_prompt_final(
    numero,
    enunciado,
    alternativa_correta,
    descricao_visual,
    respostas_base
):

    if descricao_visual:

        bloco_visual = f"""
============================================================
ELEMENTOS VISUAIS DA QUESTÃO
============================================================

{descricao_visual}
"""

    else:

        bloco_visual = ""


    if respostas_base:

        textos = []

        for i, base in enumerate(
            respostas_base,
            start=1
        ):

            textos.append(
                f"""
============================================================
RESPOSTA-BASE {i}
============================================================

{base["texto"]}
"""
            )


        bloco_bases = (
            "\n".join(
                textos
            )
        )

    else:

        bloco_bases = """
============================================================
RESPOSTAS-BASE
============================================================

Nenhuma resposta-base elegível foi selecionada.

Produza uma nova resolução independente.
"""


    prompt = f"""
{PROMPT_FINALIZADOR}

============================================================
DADOS DA QUESTÃO
============================================================

Número:
{numero}

Alternativa correta:
{alternativa_correta}

Enunciado:
{enunciado}

{bloco_visual}

{bloco_bases}

============================================================
INSTRUÇÃO FINAL
============================================================

Produza agora o gabarito comentado final da Questão {numero}.

A resolução deve começar exatamente com:

QUESTÃO {numero} — Alternativa {alternativa_correta}
"""


    return prompt.strip()



def gerar_gabarito_final(prompt):

    ultimo_erro = None


    for tentativa in range(
        1,
        MAX_TENTATIVAS + 1
    ):

        try:

            resposta = (
                client.chat.completions.create(
                    model=MODELO_FINALIZADOR,

                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],

                    reasoning_effort="medium",

                    temperature=0.3,

                    max_completion_tokens=2200,

                    stream=False
                )
            )


            texto = (
                resposta
                .choices[0]
                .message
                .content
                .strip()
            )


            return texto


        except Exception as erro:

            ultimo_erro = erro

            print(
                f"  Tentativa final "
                f"{tentativa} falhou:"
            )

            print(
                f"  {type(erro).__name__}: "
                f"{erro}"
            )


            if tentativa < MAX_TENTATIVAS:

                espera = (
                    15 * tentativa
                )

                print(
                    f"  Aguardando "
                    f"{espera}s..."
                )

                time.sleep(
                    espera
                )


    raise ultimo_erro



def validar_gabarito(
    texto,
    numero,
    alternativa
):

    problemas = []


    cabecalho = (
        f"QUESTÃO {numero} "
        f"— Alternativa {alternativa}"
    )


    if cabecalho not in texto:

        problemas.append(
            "Cabeçalho esperado ausente."
        )


    if "Comentário geral" not in texto:

        problemas.append(
            "Seção Comentário geral ausente."
        )


    if (
        "Análise das alternativas"
        not in texto
    ):

        problemas.append(
            "Seção Análise das alternativas ausente."
        )


    for letra in [
        "A)",
        "B)",
        "C)",
        "D)",
        "E)"
    ]:

        if letra not in texto:

            problemas.append(
                f"Alternativa {letra} ausente."
            )


    termos_proibidos = [
        "ChatGPT",
        "Gemini",
        "Claude",
        "Groq",
        "Judge",
        "resposta-base",
        "LLM"
    ]


    for termo in termos_proibidos:

        if termo.lower() in texto.lower():

            problemas.append(
                f"Termo proibido encontrado: "
                f"{termo}"
            )


    return problemas



def salvar_json_final(
    numero,
    dados
):

    PASTA_JSON_FINAL.mkdir(
        parents=True,
        exist_ok=True
    )


    caminho = (
        PASTA_JSON_FINAL
        / f"q{int(numero):02d}_final.json"
    )


    with open(
        caminho,
        "w",
        encoding="utf-8"
    ) as arquivo:

        json.dump(
            dados,
            arquivo,
            ensure_ascii=False,
            indent=2
        )



print()
print(
    "=============================================="
)
print(
    f"GABARITO FINAL ENADE {ANO}"
)
print(
    "=============================================="
)
print()

print(
    f"Finalizador: {MODELO_FINALIZADOR}"
)
print(
    f"Modelo de visão: {MODELO_VISAO}"
)
print()



print(
    "Carregando planilhas..."
)


questoes = pd.read_excel(
    ARQUIVO_DADOS,
    sheet_name="Questões"
)

respostas_originais = pd.read_excel(
    ARQUIVO_DADOS,
    sheet_name="Respostas LLM"
)

gabaritos = pd.read_excel(
    ARQUIVO_DADOS,
    sheet_name="Gabarito_INEP"
)


avaliacoes = pd.read_excel(
    ARQUIVO_JUDGE,
    sheet_name="Avaliacoes"
)

resumo_judge = pd.read_excel(
    ARQUIVO_JUDGE,
    sheet_name="Resumo"
)


questoes = normalizar_colunas(
    questoes
)

respostas_originais = (
    normalizar_colunas(
        respostas_originais
    )
)

gabaritos = normalizar_colunas(
    gabaritos
)

avaliacoes = normalizar_colunas(
    avaliacoes
)

resumo_judge = normalizar_colunas(
    resumo_judge
)


print(
    "Planilhas carregadas."
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

respostas_originais["Questão"] = respostas_originais["Questão"].apply(
    normalizar_numero_questao
)

gabaritos["Questão"] = gabaritos["Questão"].apply(
    normalizar_numero_questao
)

avaliacoes["Questão"] = avaliacoes["Questão"].apply(
    normalizar_numero_questao
)

resumo_judge["Questão"] = resumo_judge["Questão"].apply(
    normalizar_numero_questao
)
print()



numeros = (
    resumo_judge[
        "Questão"
    ]
    .dropna()
    .astype(int)
    .sort_values()
    .tolist()
)


if QUESTOES_PROCESSAR is not None:

    numeros = [
        numero
        for numero in numeros
        if numero
        in QUESTOES_PROCESSAR
    ]


print(
    f"Questões a processar: "
    f"{len(numeros)}"
)

print(
    numeros
)

print()



linhas_resultado = []

linhas_erros = []



for posicao, numero in enumerate(
    numeros,
    start=1
):

    print(
        "----------------------------------------------"
    )

    print(
        f"[{posicao}/{len(numeros)}] "
        f"Questão {numero}"
    )


    try:


        linha_q = questoes[
            questoes[
                "Questão"
            ].astype("Int64")
            == numero
        ]


        if linha_q.empty:

            raise ValueError(
                "Questão não encontrada "
                "na aba Questões."
            )


        enunciado = texto_seguro(
            linha_q.iloc[0][
                "Enunciado"
            ]
        )


        situacao = ""

        if "Situação" in linha_q.columns:

            situacao = texto_seguro(
                linha_q.iloc[0][
                    "Situação"
                ]
            )



        if situacao.lower() == "anulada":

            texto_final = (
                "QUESTÃO ANULADA"
            )


            linhas_resultado.append(
                {
                    "Questão":
                        numero,

                    "Gabarito INEP":
                        "",

                    "Origem da base":
                        "Questão anulada",

                    "Respostas utilizadas":
                        "",

                    "Modelos utilizados":
                        "",

                    "Possui figura":
                        "",

                    "Validação automática":
                        "OK",

                    "Gabarito comentado final":
                        texto_final
                }
            )


            print(
                "  Questão anulada."
            )

            continue



        linha_gabarito = gabaritos[
            gabaritos[
                "Questão"
            ].astype("Int64")
            == numero
        ]


        if linha_gabarito.empty:

            raise ValueError(
                "Gabarito INEP não encontrado."
            )


        alternativa_correta = (
            normalizar_alternativa(
                linha_gabarito.iloc[0][
                    "Gabarito INEP"
                ]
            )
        )



        linha_resumo = resumo_judge[
            resumo_judge[
                "Questão"
            ].astype("Int64")
            == numero
        ]


        if linha_resumo.empty:

            raise ValueError(
                "Resumo do Judge "
                "não encontrado."
            )


        linha_resumo = (
            linha_resumo.iloc[0]
        )



        avaliacoes_q = avaliacoes[
            avaliacoes[
                "Questão"
            ].astype("Int64")
            == numero
        ].copy()



        codigos = codigos_da_base(
            linha_resumo,
            avaliacoes_q
        )


        respostas_base = (
            recuperar_respostas_base(
                numero,
                codigos,
                avaliacoes_q,
                respostas_originais
            )
        )


        if respostas_base:

            if len(respostas_base) == 1:

                origem_base = (
                    "Resposta-base"
                )

            else:

                origem_base = (
                    "Síntese"
                )

        else:

            origem_base = (
                "Nova resolução"
            )


        print(
            f"  Gabarito: "
            f"{alternativa_correta}"
        )

        print(
            f"  Origem: "
            f"{origem_base}"
        )

        if codigos:

            print(
                "  Bases: "
                + "+".join(
                    codigos
                )
            )

        else:

            print(
                "  Bases: nenhuma"
            )



        imagens = localizar_imagens(
            numero
        )


        if imagens:

            print(
                "  Imagens:"
            )

            for imagem in imagens:

                print(
                    f"    - {imagem.name}"
                )


            descricao_visual = (
                descrever_imagens(
                    numero,
                    enunciado,
                    imagens
                )
            )

        else:

            print(
                "  Sem imagem."
            )

            descricao_visual = ""



        prompt = montar_prompt_final(
            numero,
            enunciado,
            alternativa_correta,
            descricao_visual,
            respostas_base
        )


        print(
            "  Gerando gabarito comentado..."
        )


        texto_final = (
            gerar_gabarito_final(
                prompt
            )
        )



        problemas = validar_gabarito(
            texto_final,
            numero,
            alternativa_correta
        )


        if problemas:

            validacao = (
                "REVISAR: "
                + " | ".join(
                    problemas
                )
            )

            print(
                "  ⚠ Validação requer revisão."
            )

            for problema in problemas:

                print(
                    f"    - {problema}"
                )

        else:

            validacao = "OK"

            print(
                "  ✓ Validação automática OK."
            )



        modelos_usados = ", ".join(
            [
                base["llm"]
                for base
                in respostas_base
            ]
        )


        codigos_usados = "+".join(
            [
                base["codigo"]
                for base
                in respostas_base
            ]
        )



        dados_json = {
            "ano":
                ANO,

            "questao":
                numero,

            "alternativa_correta":
                alternativa_correta,

            "origem_base":
                origem_base,

            "respostas_anonimas_utilizadas":
                codigos_usados,

            "modelos_origem":
                modelos_usados,

            "imagens":
                [
                    imagem.name
                    for imagem
                    in imagens
                ],

            "descricao_visual":
                descricao_visual,

            "validacao":
                problemas,

            "gabarito_comentado_final":
                texto_final,

            "modelo_finalizador":
                MODELO_FINALIZADOR,

            "data":
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
        }


        salvar_json_final(
            numero,
            dados_json
        )



        linhas_resultado.append(
            {
                "Questão":
                    numero,

                "Gabarito INEP":
                    alternativa_correta,

                "Origem da base":
                    origem_base,

                "Respostas utilizadas":
                    (
                        codigos_usados
                        if codigos_usados
                        else "Nenhuma"
                    ),

                "Modelos utilizados":
                    (
                        modelos_usados
                        if modelos_usados
                        else "Nenhum"
                    ),

                "Possui figura":
                    (
                        "Sim"
                        if imagens
                        else "Não"
                    ),

                "Validação automática":
                    validacao,

                "Gabarito comentado final":
                    texto_final
            }
        )


        print(
            "  ✓ Questão concluída."
        )


    except Exception as erro:

        print(
            "  ✗ ERRO:"
        )

        print(
            f"    {type(erro).__name__}: "
            f"{erro}"
        )


        linhas_erros.append(
            {
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



    PASTA_RESULTADOS.mkdir(
        parents=True,
        exist_ok=True
    )


    df_resultado = pd.DataFrame(
        linhas_resultado
    )


    df_erros = pd.DataFrame(
        linhas_erros
    )


    with pd.ExcelWriter(
        ARQUIVO_SAIDA,
        engine="openpyxl"
    ) as writer:

        df_resultado.to_excel(
            writer,
            sheet_name="Gabarito Final",
            index=False
        )

        df_erros.to_excel(
            writer,
            sheet_name="Erros",
            index=False
        )


    print(
        "  Checkpoint salvo."
    )

    print()


    if (
        posicao
        < len(numeros)
    ):

        time.sleep(
            INTERVALO_ENTRE_QUESTOES
        )



print()
print(
    "=============================================="
)

print(
    "GABARITO FINAL CONCLUÍDO"
)

print(
    "=============================================="
)

print()

print(
    f"Questões concluídas: "
    f"{len(linhas_resultado)}"
)

print(
    f"Questões com erro: "
    f"{len(linhas_erros)}"
)

print()

print(
    f"Arquivo:"
)

print(
    ARQUIVO_SAIDA
)

print()