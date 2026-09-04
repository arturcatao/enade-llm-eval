def montar_prompt(questao) -> str:

    numero_questao = int(questao["numero_da_questao"])

    enunciado = questao["Enunciado"]
    gabarito_inep = questao["Gabarito INEP"]
    gabarito_comentado = questao["Gabarito comentado final"]

    prompt = f"""
Você atuará como professor e avaliador especialista na correção de
questões objetivas de nível superior do ENADE 2021.

Sua tarefa é avaliar a resposta fornecida para a questão, comparando-a
com o gabarito oficial do INEP e com o comentário oficial fornecido.

Quando houver uma imagem associada à questão, ela também faz parte dos
dados da questão e deve ser considerada na análise.

Não faça pesquisas na internet.

==================================================
CRITÉRIOS DE AVALIAÇÃO
==================================================

1. SE_ACERTOU

Verifique se a alternativa escolhida na resposta fornecida corresponde
ao gabarito oficial do INEP.

Retorne:

- "SIM" se corresponde ao gabarito.
- "NAO" caso contrário.

2. EXPLICACAO_TA_BOA

Avalie se a explicação fornecida está tecnicamente correta, clara,
objetiva e suficientemente detalhada.

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
- "NAO" se estiver incorreta, incompleta, superficial, confusa ou
  insuficiente.

3. SEM_RASTRO_LLM

Avalie se a resposta apresenta uma redação natural e compatível com
uma resposta humana, sem características evidentes de texto gerado
por LLM.

Retorne:

- "SIM" se parecer natural e humana.
- "NAO" se apresentar sinais evidentes de texto artificial, robótico,
  genérico ou excessivamente padronizado.

4. ACORDO_COM_INEP

Verifique se a resposta está de acordo com o gabarito oficial do INEP
e com o gabarito comentado fornecido.

Retorne:

- "SIM" se estiver de acordo e não apresentar erro conceitual relevante.
- "NAO" se houver contradição, erro conceitual relevante ou conclusão
  incompatível com o gabarito oficial.

5. ANULADA_TEM_EXPLICACAO

Verifique a situação oficial da questão.

Se a questão NÃO estiver anulada:

- retorne exatamente null.

Se a questão estiver anulada:

- retorne "SIM" se a resposta identificar que a questão foi anulada
  e explicar adequadamente o motivo;
- retorne "NAO" caso contrário.

IMPORTANTE:

null significa que o critério não se aplica.

Não considere null como "NAO".

==================================================
REGRA PARA EXPLICACAO_FINAL
==================================================

Se TODOS os critérios aplicáveis forem "SIM", mantenha a resposta
fornecida EXATAMENTE como foi apresentada.

Não corrija, resuma ou altere a resposta nesse caso.

Se QUALQUER critério aplicável for "NAO", substitua completamente a
explicação fornecida por uma nova resolução.

A explicação final deve ser uma resolução objetiva e técnica da questão,
como se fosse produzida por um professor especialista.

A resolução deve seguir esta estrutura conceitual:

Você atuará como especialista na resolução de questões objetivas de nível superior.

Resolva a questão apresentada de maneira independente.

IMPORTANTE:

- Não utilize pesquisa na internet, ferramentas de busca, fontes externas, gabaritos ou respostas previamente publicadas.
- Não tente identificar ou inferir a origem da questão ou seu gabarito oficial.
- Baseie sua resposta exclusivamente no enunciado, nas alternativas e no conhecimento necessário para resolver a questão.
- Se houver inconsistência, insuficiência de informação ou possível ambiguidade, sinalize-a.
- Não utilize respostas anteriores ou respostas produzidas por outros modelos.
- Resolva a questão de forma clara, técnica e suficientemente detalhada.

A resolução deve ser escrita como um comentário de professor especialista, explicando o raciocínio necessário para chegar à resposta correta.

Apresente a resolução seguindo esta estrutura:

QUESTÃO [número] — Alternativa [alternativa correta]

Comentário geral

Apresente uma explicação geral sobre o que a questão aborda e os principais conceitos necessários para resolvê-la.

Em seguida, analise as afirmações ou elementos apresentados no enunciado, quando houver, explicando quais estão corretos ou incorretos e justificando tecnicamente cada conclusão.

Ao final dessa parte, apresente claramente qual alternativa está correta e por quê.

Análise das alternativas

A) Explique por que a alternativa está correta ou incorreta. Apresente o raciocínio necessário para justificar a conclusão.

B) Explique por que a alternativa está correta ou incorreta. Apresente o raciocínio necessário para justificar a conclusão.

C) Explique por que a alternativa está correta ou incorreta. Apresente o raciocínio necessário para justificar a conclusão.

D) Explique por que a alternativa está correta ou incorreta. Apresente o raciocínio necessário para justificar a conclusão.

E) Explique por que a alternativa está correta ou incorreta. Apresente o raciocínio necessário para justificar a conclusão.

REGRAS PARA A RESOLUÇÃO:

- A resolução deve ser autocontida e compreensível para alguém que esteja estudando o conteúdo.
- Explique os conceitos necessários para compreender a resposta.
- Não seja excessivamente breve ou superficial.
- Não apenas diga que uma alternativa está errada: explique o erro.
- Quando uma alternativa for parcialmente correta, explique exatamente em que ponto ela se torna incorreta.
- Quando a questão apresentar afirmações numeradas (I, II, III etc.), analise cada uma individualmente antes de avaliar as alternativas.
- Quando for relevante, explique por que uma alternativa pode parecer plausível, mas está incorreta.
- Não invente informações que não estejam presentes no enunciado ou que não sejam necessárias para a resolução.
- Não mencione gabarito, INEP, critérios de avaliação, confiança, dificuldade, ambiguidade, força dos distratores ou qualquer outro parâmetro de avaliação na resolução.
- Não mencione que você é uma IA ou que a resposta foi gerada por um modelo.
- Escreva naturalmente, como um professor explicando a resolução para um aluno.

A resolução deve conter somente o conteúdo necessário para explicar a questão e justificar a alternativa correta.

IMPORTANTE:

A resolução acima deve ser retornada como uma única STRING no campo "explicacao_final".

Não transforme "explicacao_final" em um objeto JSON.

As quebras de linha da resolução devem ser representadas como "\n" dentro da string JSON.

Não inclua dentro de "explicacao_final" nenhum dos parâmetros de avaliação utilizados para gerar os demais campos da resposta.

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

Quando a questão não for anulada, use null sem aspas no campo
anulada_tem_explicacao.

==================================================
DADOS DA QUESTÃO
==================================================

Número da questão:
{numero_questao}

Enunciado:
{enunciado}

Gabarito oficial do INEP:
{gabarito_inep}

Gabarito comentado final:
{gabarito_comentado}

==================================================
FIM DOS DADOS
==================================================
"""

    return prompt