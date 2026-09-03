def montar_prompt(questao) -> str:
    numero_questao = int(questao["numero_da_questao"])
    enunciado = questao["enunciado"]
    gabarito_inep = questao["gabarito_inep"]
    resposta_original = questao["resposta_original"]

    prompt = f"""
Você atuará como professor e avaliador especialista na correção de questões objetivas de nível superior do ENADE 2021.

Sua tarefa é avaliar a resposta original fornecida para a questão, comparando-a com o gabarito oficial do INEP e com os dados fornecidos.

Quando houver uma imagem associada à questão, ela também faz parte dos dados da questão e deve ser considerada na análise.

Não faça pesquisas na internet.

==================================================
CRITÉRIOS DE AVALIAÇÃO
==================================================

Avalie a resposta original segundo os seguintes critérios:

1. SE_ACERTOU

A alternativa escolhida na resposta original corresponde ao gabarito oficial do INEP?

Retorne:
- "SIM" se corresponde ao gabarito.
- "NAO" caso contrário.

2. EXPLICACAO_TA_BOA

A explicação da resposta original está tecnicamente correta, clara, objetiva e suficientemente detalhada?

Considere se a explicação justifica adequadamente a alternativa escolhida e, quando necessário, explica por que as demais alternativas estão incorretas.

Retorne:
- "SIM" se a explicação for adequada.
- "NAO" se estiver incorreta, incompleta, superficial, confusa ou insuficiente.

3. SEM_RASTRO_LLM

A resposta original apresenta uma redação natural e compatível com uma resposta humana, sem características evidentes de texto gerado por LLM?

Retorne:
- "SIM" se parecer natural e humana.
- "NAO" se apresentar sinais evidentes de texto artificial, robótico, genérico ou excessivamente padronizado.

4. ACORDO_COM_INEP

A resposta original está de acordo com o gabarito oficial do INEP e não apresenta nenhuma afirmação que contradiga a resposta oficial?

Retorne:
- "SIM" se estiver de acordo.
- "NAO" se houver contradição ou erro conceitual relevante.

5. ANULADA_TEM_EXPLICACAO

Verifique se a questão foi anulada.

Se a questão NÃO estiver anulada:
- retorne exatamente null.

Se a questão estiver anulada:
- retorne "SIM" se a resposta original identificar a anulação e explicar adequadamente o motivo;
- retorne "NAO" caso contrário.

IMPORTANTE:
null significa que o critério não se aplica.
Não considere null como "NAO".

==================================================
FORMATO DE SAÍDA
==================================================

Sua resposta DEVE ser exclusivamente um array JSON válido contendo exatamente 7 elementos, nesta ordem:

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

Quando a questão não for anulada, use null sem aspas no campo anulada_tem_explicacao.

==================================================
REGRAS DA EXPLICACAO_FINAL
==================================================

Se TODOS os critérios aplicáveis forem "SIM", mantenha a resposta original EXATAMENTE como foi fornecida.

Não corrija, resuma ou altere a resposta original nesse caso.

Se QUALQUER critério aplicável for "NAO", refaça completamente a explicação.

A nova explicação deve ser escrita como uma resolução objetiva e técnica da questão, como se fosse produzida por um professor especialista.

A resolução refeita deve:

- indicar claramente a alternativa correta;
- explicar por que ela está correta;
- explicar os conceitos necessários para resolver a questão;
- quando for relevante, explicar por que as demais alternativas estão incorretas;
- corrigir eventuais erros presentes na resposta original;
- não mencionar que a resposta original estava errada;
- não mencionar inteligência artificial, LLM ou este processo de avaliação;
- não incluir métricas de confiança;
- não incluir dificuldade;
- não incluir análise de ambiguidade;
- não incluir força dos distratores;
- não incluir metacomentários sobre a avaliação;
- não incluir informações fora do necessário para resolver a questão.

A resolução deve ser natural, clara e semelhante a uma resposta humana de prova ou comentário de gabarito.

Se a questão estiver anulada, a explicação deve informar que a questão foi anulada e explicar tecnicamente o motivo da anulação.

==================================================
DADOS DA QUESTÃO
==================================================

Número da Questão:
{numero_questao}

Enunciado:
{enunciado}

Gabarito oficial do INEP:
{gabarito_inep}

Resposta original a ser avaliada:
{resposta_original}

==================================================
FIM DOS DADOS DA QUESTÃO
==================================================
"""

    return prompt