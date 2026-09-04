def montar_prompt(dados: dict) -> str:
    """
    Monta o prompt enviado ao Mistral.

    `dados` é um dicionário com os campos já resolvidos pelo main.py
    (nenhum dado objetivo deve ser inferido ou inventado pelo modelo):

      - numero               (int)
      - enunciado            (str)
      - gabarito_inep        (str ou None)
      - situacao_oficial     (str ou None)
      - resposta_avaliada    (str ou None)  -- vem da coluna
                                                "Gabarito comentado final"
      - modelo_base          (str ou None)

    Não existe, separadamente, um "gabarito comentado oficial" para
    comparação: a única referência autorizada para a alternativa
    correta é `gabarito_inep`.
    """

    numero_questao = dados["numero"]
    enunciado = dados["enunciado"]

    gabarito_inep = dados.get("gabarito_inep")
    if gabarito_inep is None or str(gabarito_inep).strip() == "":
        texto_gabarito_inep = (
            "[NÃO INFORMADO — não existe Gabarito INEP cadastrado "
            "para esta questão]"
        )
    else:
        texto_gabarito_inep = str(gabarito_inep).strip()

    situacao_oficial = dados.get("situacao_oficial")
    if situacao_oficial is None or str(situacao_oficial).strip() == "":
        texto_situacao = "[NÃO INFORMADA]"
    else:
        texto_situacao = str(situacao_oficial).strip()

    resposta_avaliada = dados.get("resposta_avaliada")
    if resposta_avaliada is None or str(resposta_avaliada).strip() == "":
        texto_resposta_avaliada = (
            "[NENHUMA RESPOSTA FOI FORNECIDA PARA ESTA QUESTÃO — "
            "NÃO EXISTE RESPOSTA PARA AVALIAR]"
        )
    else:
        texto_resposta_avaliada = str(resposta_avaliada).strip()

    modelo_base = dados.get("modelo_base")
    if modelo_base is None or str(modelo_base).strip() == "":
        texto_modelo_base = "Não informado"
    else:
        texto_modelo_base = str(modelo_base).strip()

    prompt = f"""
Você atuará como professor e avaliador especialista na correção de
questões objetivas de nível superior do ENADE 2021.

Sua tarefa é avaliar a RESPOSTA AVALIADA (fornecida abaixo, nos DADOS DA
QUESTÃO) para a questão indicada, comparando-a com o Gabarito INEP,
também fornecido abaixo — a única referência oficial disponível para a
alternativa correta.

Todos os dados objetivos desta tarefa (enunciado, resposta avaliada,
gabarito INEP, situação oficial da questão) são fornecidos
explicitamente abaixo, na seção DADOS DA QUESTÃO. Você NUNCA
deve inventar, presumir ou completar qualquer um desses dados. Se um
dado não foi fornecido, ele está marcado como tal explicitamente — trate
isso como um fato, não como algo a ser deduzido.

Quando houver uma imagem associada à questão, ela também faz parte dos
dados da questão e deve ser considerada na análise.

Não faça pesquisas na internet nem utilize fontes externas para avaliar
os critérios abaixo. Isso NÃO impede o uso do Gabarito INEP fornecido
nos DADOS DA QUESTÃO — ele é um dado oficial fornecido diretamente para
esta tarefa, e não pesquisa externa. Use-o normalmente para os
critérios que o exigem.

==================================================
REGRA CRÍTICA: RESPOSTA AVALIADA AUSENTE
==================================================

Se o campo "Resposta avaliada" abaixo indicar que NENHUMA resposta foi
fornecida, você DEVE:

- se_acertou = "NAO"
- explicacao_ta_boa = "NAO"
- sem_rastro_llm = "NAO"
- acordo_com_inep = "NAO"

Nunca retorne "SIM" para nenhum desses quatro campos quando não houver
resposta avaliada. Não existe cenário em que a ausência de resposta
resulte em "tudo correto". Mesmo nesse caso, gere normalmente a
explicacao_final como a resolução técnica da questão (ver regra
específica mais abaixo), sem mencionar a ausência de resposta dentro do
texto da explicacao_final.

==================================================
REGRA CRÍTICA: GABARITO INEP AUSENTE
==================================================

Se o campo "Gabarito INEP" abaixo indicar que ele não foi informado,
você DEVE:

- acordo_com_inep = "NAO"
- se_acertou = "NAO"

Nunca invente ou deduza qual seria o gabarito oficial nesse caso.

==================================================
REGRA CRÍTICA: SITUAÇÃO OFICIAL DA QUESTÃO
==================================================

O campo "Situação oficial" abaixo já informa, de forma definitiva, se a
questão está anulada ou regular. Você NÃO deve tentar descobrir ou
inferir isso por conta própria a partir do enunciado ou do gabarito
comentado — use exclusivamente o valor fornecido nesse campo.

- Se a Situação oficial NÃO for "Anulada", retorne exatamente null no
  campo anulada_tem_explicacao (o critério não se aplica).
- Se a Situação oficial FOR "Anulada", avalie se a resposta avaliada
  identifica isso e explica o motivo adequadamente, retornando "SIM" ou
  "NAO".

==================================================
CRITÉRIOS DE AVALIAÇÃO
==================================================

1. SE_ACERTOU

Verifique se a alternativa escolhida na resposta avaliada corresponde
ao Gabarito INEP.

Retorne:

- "SIM" se corresponde ao gabarito.
- "NAO" caso contrário (inclusive se não houver resposta avaliada ou
  não houver Gabarito INEP, conforme regras críticas acima).

2. EXPLICACAO_TA_BOA

Avalie se a explicação contida na resposta avaliada está tecnicamente
correta, clara, objetiva e suficientemente detalhada.

Considere se ela:

- justifica adequadamente a alternativa escolhida;
- apresenta os conceitos necessários;
- não contém erros conceituais;
- possui explicação suficiente para compreender por que a alternativa
  está correta.

Quando for relevante, também pode explicar por que as demais
alternativas estão incorretas.

Retorne:

- "SIM" se a explicação for adequada.
- "NAO" se estiver incorreta, incompleta, superficial, confusa,
  insuficiente ou ausente.

3. SEM_RASTRO_LLM

Avalie se a resposta avaliada apresenta uma redação natural e
compatível com uma resposta humana, sem características evidentes de
texto gerado por LLM.

Retorne:

- "SIM" se parecer natural e humana.
- "NAO" se apresentar sinais evidentes de texto artificial, robótico,
  genérico, excessivamente padronizado, ou se não houver resposta para
  avaliar.

4. ACORDO_COM_INEP

Verifique se a resposta avaliada está de acordo com o Gabarito INEP
fornecido (a única referência oficial disponível para a alternativa
correta) e se não apresenta erro conceitual relevante.

Retorne:

- "SIM" se estiver de acordo e não apresentar erro conceitual relevante.
- "NAO" se houver contradição, erro conceitual relevante, conclusão
  incompatível com o Gabarito INEP, ausência de resposta ou ausência
  de Gabarito INEP.

5. ANULADA_TEM_EXPLICACAO

Aplique exatamente a REGRA CRÍTICA: SITUAÇÃO OFICIAL DA QUESTÃO descrita
acima.

null significa que o critério não se aplica. Não considere null como
"NAO".

==================================================
REGRA PARA EXPLICACAO_FINAL
==================================================

Se TODOS os critérios aplicáveis (se_acertou, explicacao_ta_boa,
sem_rastro_llm, acordo_com_inep e, quando aplicável,
anulada_tem_explicacao) forem "SIM", mantenha a resposta avaliada
EXATAMENTE como foi apresentada em explicacao_final. Não corrija, resuma
ou altere a resposta nesse caso.

Se QUALQUER critério aplicável for "NAO", substitua completamente a
explicação fornecida por uma nova resolução, seguindo a estrutura
abaixo.

A explicação final deve ser uma resolução objetiva e técnica da questão,
como se fosse produzida por um professor especialista, escrita de forma
independente — não copie literalmente o texto da resposta avaliada,
mesmo que use a mesma alternativa correta como referência.

IMPORTANTE:

- Baseie sua resposta exclusivamente no enunciado, nas alternativas, no
  Gabarito INEP fornecido (para saber qual é a alternativa correta) e
  no conhecimento necessário para resolver a questão.
- Não tente identificar ou inferir a origem da questão.
- Se houver inconsistência, insuficiência de informação ou possível
  ambiguidade no enunciado, sinalize-a.
- Nunca invente uma alternativa correta que não esteja de acordo com o
  Gabarito INEP fornecido. Se o Gabarito INEP não foi informado, deixe
  claro na resolução que não há gabarito oficial disponível para esta
  questão, em vez de apontar uma alternativa como correta.

A resolução deve ser escrita como um comentário de professor
especialista, explicando o raciocínio necessário para chegar à resposta
correta.

Apresente a resolução seguindo esta estrutura:

QUESTÃO [número] — Alternativa [alternativa correta]

Comentário geral

Apresente uma explicação geral sobre o que a questão aborda e os
principais conceitos necessários para resolvê-la.

Em seguida, analise as afirmações ou elementos apresentados no
enunciado, quando houver, explicando quais estão corretos ou incorretos
e justificando tecnicamente cada conclusão.

Ao final dessa parte, apresente claramente qual alternativa está correta
e por quê.

Análise das alternativas

A) Explique por que a alternativa está correta ou incorreta. Apresente
o raciocínio necessário para justificar a conclusão.

B) Explique por que a alternativa está correta ou incorreta. Apresente
o raciocínio necessário para justificar a conclusão.

C) Explique por que a alternativa está correta ou incorreta. Apresente
o raciocínio necessário para justificar a conclusão.

D) Explique por que a alternativa está correta ou incorreta. Apresente
o raciocínio necessário para justificar a conclusão.

E) Explique por que a alternativa está correta ou incorreta. Apresente
o raciocínio necessário para justificar a conclusão.

REGRAS PARA A RESOLUÇÃO:

- A resolução deve ser autocontida e compreensível para alguém que
  esteja estudando o conteúdo.
- Explique os conceitos necessários para compreender a resposta.
- Não seja excessivamente breve ou superficial.
- Não apenas diga que uma alternativa está errada: explique o erro.
- Quando uma alternativa for parcialmente correta, explique exatamente
  em que ponto ela se torna incorreta.
- Quando a questão apresentar afirmações numeradas (I, II, III etc.),
  analise cada uma individualmente antes de avaliar as alternativas.
- Quando for relevante, explique por que uma alternativa pode parecer
  plausível, mas está incorreta.
- Não invente informações que não estejam presentes no enunciado ou que
  não sejam necessárias para a resolução.
- Não mencione gabarito, INEP, critérios de avaliação, confiança,
  dificuldade, ambiguidade, força dos distratores, ausência de resposta
  ou qualquer outro parâmetro de avaliação dentro da resolução.
- Não mencione que você é uma IA ou que a resposta foi gerada por um
  modelo.
- Escreva naturalmente, como um professor explicando a resolução para
  um aluno.

A resolução deve conter somente o conteúdo necessário para explicar a
questão e justificar a alternativa correta.

IMPORTANTE:

A resolução acima deve ser retornada como uma única STRING no campo
"explicacao_final". Não transforme "explicacao_final" em um objeto
JSON. As quebras de linha da resolução devem ser representadas como
"\\n" dentro da string JSON. Não inclua dentro de "explicacao_final"
nenhum dos parâmetros de avaliação utilizados para gerar os demais
campos da resposta.

==================================================
FORMATO DE SAÍDA
==================================================

Sua resposta DEVE ser exclusivamente um array JSON válido contendo
exatamente 7 elementos, nesta ordem:

[
  numero_da_questao,
  se_acertou,
  explicacao_ta_boa,
  sem_rastro_llm,
  acordo_com_inep,
  anulada_tem_explicacao,
  explicacao_final
]

Não coloque markdown.

Não coloque ```json.

Não coloque explicações antes ou depois do array.

Não coloque campos adicionais.

Use aspas duplas nas strings.

Quando anulada_tem_explicacao não se aplicar, use null sem aspas.

==================================================
DADOS DA QUESTÃO
==================================================

Número da questão:
{numero_questao}

Enunciado:
{enunciado}

Situação oficial:
{texto_situacao}

Gabarito INEP:
{texto_gabarito_inep}

Modelo que gerou a resposta avaliada (se disponível):
{texto_modelo_base}

Resposta avaliada (é esta resposta que você deve avaliar nos critérios
acima, comparando-a com o Gabarito INEP fornecido):
{texto_resposta_avaliada}

==================================================
FIM DOS DADOS
==================================================
"""

    return prompt