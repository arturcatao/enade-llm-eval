def gerar_prompt(num_questao, enunciado, gabarito_oficial, resposta_original_aqui):

    prompt = '''Você atuará como professor e avaliador especialista na correção de questões objetivas de nível superior do exame Enade 2021. Você receberá o texto da questão, o gabarito oficial do INEP, a situação da questão (válida ou anulada) e a resposta original que deve ser avaliada.

    Sua missão é avaliar a resposta fornecida com base nestes critérios:

    A resposta original acertou a alternativa, de acordo com o gabarito do INEP?

    A justificativa original está boa, explicando de maneira técnica, objetiva e suficientemente detalhada a correção da alternativa escolhida e das demais alternativas?

    O texto original está SEM rastros de LLM (possui tom humano e natural, sem clichês óbvios de inteligência artificial)?

    A resposta original está perfeitamente de acordo com o gabarito oficial do INEP?

    Se a questão foi anulada pelo INEP, a resposta original detectou isso e explicou o motivo técnico da anulação de forma clara?

    Formato de Saída Exigido:
    Você DEVE retornar APENAS uma lista (array) contendo exatamente 7 elementos na seguinte ordem, sem nenhum texto adicional antes ou depois (como formatação markdown para blocos de código):

    [numero_da_questao, se_acertou, explicacao_ta_boa, sem_rastro_llm, acordo_com_inep, anulada_tem_explicacao, explicacao_final]

    Regras rigorosas de preenchimento da lista:

    numero_da_questao: (Inteiro) O número da questão avaliada extraído do enunciado.

    se_acertou: (String) "SIM" ou "NAO".

    explicacao_ta_boa: (String) "SIM" ou "NAO".

    sem_rastro_llm: (String) "SIM" (se o texto parecer humano e natural) ou "NAO" (se parecer robótico/IA/incompleto em relação ao template exigido).

    acordo_com_inep: (String) "SIM" ou "NAO".

    anulada_tem_explicacao: (String) "SIM", "NAO" ou null (se a questão NÃO for anulada, o valor deve ser exatamente null).

    explicacao_final: (String)

    Se TODOS os parâmetros avaliativos acima forem "SIM" (ou null no caso da anulação), copie exatamente a resposta original que foi dada.

    Se QUALQUER UM dos parâmetros for "NAO", você deve REFAZER totalmente a resposta, simulando a resolução de um especialista humano para que todos os parâmetros fiquem "SIM".

    SE FOR NECESSÁRIO REFAZER A EXPLICAÇÃO FINAL, a nova string em explicacao_final deve OBRIGATORIAMENTE seguir o template abaixo, usando barras de escape \n para quebras de linha dentro da string da lista. Não use pesquisa na internet nem adicione comentários fora do template.

    Template obrigatório caso precise refazer a explicação_final:

    ALTERNATIVA ESCOLHIDA:
    [A, B, C, D ou E - Baseie-se no gabarito do INEP. Se for anulada, escreva: ANULADA]

    CONFIANÇA AUTODECLARADA:
    [valor inteiro de 0 a 100]

    DIFICULDADE:
    [valor inteiro de 1 a 5, sendo 1=Muito fácil, 2=Fácil, 3=Média, 4=Difícil, 5=Muito difícil]

    AMBIGUIDADE:
    [valor inteiro de 0 a 2, sendo 0=Sem ambiguidade, 1=Ambiguidade menor, 2=Ambiguidade relevante]

    FORÇA DOS DISTRATORES:
    [valor inteiro de 0 a 2, sendo 0=Distratores fracos, 1=Distratores moderados, 2=Distratores fortes]

    TEMA PRINCIPAL:
    [tema]

    SUBTEMA:
    [subtema]

    JUSTIFICATIVA DA RESPOSTA:
    [Explique de maneira técnica, objetiva e detalhada por que a alternativa oficial/anulação está correta, baseado no INEP, sem clichês de IA]

    ANÁLISE DAS ALTERNATIVAS:
    A:
    [Explique por que está correta ou incorreta]
    B:
    [Explique por que está correta ou incorreta]
    C:
    [Explique por que está correta ou incorreta]
    D:
    [Explique por que está correta ou incorreta]
    E:
    [Explique por que está correta ou incorreta]

    JUSTIFICATIVA DA AMBIGUIDADE:
    [Explique por que atribuiu o nível 0, 1 ou 2]

    JUSTIFICATIVA DOS DISTRATORES:
    [Explique por que atribuiu o nível 0, 1 ou 2]

    [INÍCIO DOS DADOS DA AVALIAÇÃO]
    Número da Questão: {num_questao}
    Questão:
    {enunciado}
    Gabarito INEP: {gabarito_oficial}
    Resposta a ser avaliada:
    {resposta_original}
    [FIM DOS DADOS]'''

    return prompt