def montar_prompt_arbitragem(dados: dict) -> str:
    """
    Monta o prompt para a etapa de arbitragem.
    Recebe um dicionário com:
    - numero_questao: int
    - enunciado: str
    - gabarito_oficial: str
    - resposta_a: str
    - resposta_b: str
    - resposta_c: str
    """
    
    return f"""Você atuará como avaliador independente da qualidade de três soluções produzidas para uma questão objetiva de nível superior.

Você receberá:
1. o enunciado integral da questão;
2. o gabarito oficial;
3. três respostas anonimizadas, denominadas Resposta A, Resposta B e Resposta C.

Sua função é avaliar a qualidade técnica, lógica e pedagógica das três soluções e identificar qual delas apresenta a melhor fundamentação para servir de base à elaboração de um gabarito comentado.

IMPORTANTE:
- Não utilize pesquisa na internet, ferramentas de busca ou fontes externas.
- Baseie sua avaliação exclusivamente no enunciado, no gabarito oficial fornecido e nas três respostas apresentadas.
- Não tente identificar qual modelo produziu cada resposta.
- Não utilize informações sobre confiança, dificuldade ou ambiguidade dos modelos, mesmo que tente inferi-las.
- Avalie cada resposta de maneira independente.
- Não escolha automaticamente uma resposta apenas porque ela coincide com o gabarito oficial; avalie também a qualidade da fundamentação apresentada.
- Entretanto, para ser considerada elegível como resposta-base do gabarito comentado, a alternativa escolhida pela resposta deve coincidir com o gabarito oficial.
- Caso uma resposta apresente alternativa incorreta, ainda assim avalie normalmente sua qualidade nos critérios estabelecidos, mas classifique-a como NÃO ELEGÍVEL para servir de resposta-base.
- Considere o gabarito oficial como referência institucional.
- Caso identifique possível inconsistência relevante entre o enunciado e o gabarito oficial, sinalize-a e recomende revisão humana, sem substituir unilateralmente o gabarito.
- É permitido declarar empate técnico entre duas ou mais respostas quando não houver diferença relevante de qualidade.
- Não force a escolha de uma única resposta quando houver empate técnico justificável.

Avalie separadamente as Respostas A, B e C segundo os seguintes critérios, atribuindo de 0 a 5 pontos em cada um:

1. CORREÇÃO CONCEITUAL (0 a 5)
2. COERÊNCIA LÓGICA (0 a 5)
3. FUNDAMENTAÇÃO (0 a 5)
4. ANÁLISE DOS DISTRATORES (0 a 5)
5. CLAREZA PEDAGÓGICA (0 a 5)
6. ADERÊNCIA AO ENUNCIADO (0 a 5)

Para cada resposta utilize obrigatoriamente o seguinte formato:

RESPOSTA A
- Alternativa escolhida: 
- Correção conceitual: X/5
- Coerência lógica: X/5
- Fundamentação: X/5
- Análise dos distratores: X/5
- Clareza pedagógica: X/5
- Aderência ao enunciado: X/5
- Total: X/30
- Elegível como resposta-base: [Sim ou Não]
- Principal qualidade: 
- Principal problema: 

Repita exatamente a mesma estrutura para RESPOSTA B e RESPOSTA C.

Após avaliar as três respostas, apresente as conclusões rigorosamente nestes rótulos:

RESPOSTAS ELEGÍVEIS PARA O GABARITO COMENTADO:
[indique A, B, C, combinações entre elas ou Nenhuma]

MELHOR RESPOSTA PARA SERVIR DE BASE AO GABARITO COMENTADO:
[A, B, C ou EMPATE entre as respostas]

JUSTIFICATIVA DA ESCOLHA:
[Explique objetivamente]

EMPATE TÉCNICO:
[Sim ou Não]

DIVERGÊNCIAS RELEVANTES:
[Identifique erros conceituais ou discrepâncias]

RESPOSTA-BASE RECOMENDADA:
[A, B, C, SÍNTESE DE A+B, SÍNTESE DE A+C, SÍNTESE DE B+C, SÍNTESE DE A+B+C ou NENHUMA]

REVISÃO HUMANA RECOMENDADA:
[Sim ou Não]

JUSTIFICATIVA DA REVISÃO HUMANA:
[Informe objetivamente o motivo]

GABARITO COMENTADO FINAL:
[
Este campo NUNCA pode ficar vazio, resumido ou substituído por uma frase genérica quando houver uma RESPOSTA-BASE RECOMENDADA diferente de NENHUMA. Siga exatamente uma destas duas regras, sem exceção:

REGRA 1 — Se a resposta vencedora (ou cada uma das respostas usadas na síntese) já estiver tecnicamente correta, bem fundamentada e sem os problemas listados em "Principal problema": copie o texto INTEIRO dela aqui (a justificativa da resposta + a análise das alternativas, na íntegra), sem resumir, sem abreviar e sem reescrever o conteúdo. Apenas prefixe com o cabeçalho abaixo. Não escreva frases como "manter resposta original" ou "resposta já adequada" no lugar do texto — o texto completo precisa estar presente.

REGRA 2 — Se a resposta vencedora tiver qualquer problema relevante (conceitual, de fundamentação, de análise dos distratores, etc.), ou se for uma síntese de mais de uma resposta, escreva uma resolução técnica nova e completa, reaproveitando o que cada resposta usada tem de melhor.

Em ambos os casos, o texto deve obrigatoriamente começar com:
"QUESTÃO {dados['numero_questao']} — Alternativa [Letra]"

Se RESPOSTA-BASE RECOMENDADA for NENHUMA, escreva "REVISÃO NECESSÁRIA".
]

==================================================
DADOS DA QUESTÃO
==================================================

QUESTÃO:
{dados['enunciado']}

GABARITO OFICIAL:
{dados['gabarito_oficial']}

RESPOSTA A:
{dados['resposta_a']}

RESPOSTA B:
{dados['resposta_b']}

RESPOSTA C:
{dados['resposta_c']}
"""