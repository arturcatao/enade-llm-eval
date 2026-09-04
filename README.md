# Avaliação de Respostas do ENADE Computação com Mistral

Pipeline em Python que usa o Mistral (com capacidade de visão) para avaliar
automaticamente respostas geradas para questões objetivas do ENADE
Computação, comparando-as com o gabarito oficial do INEP.

## Resultados

Os resultados completos da avaliação estão disponíveis neste link:

[https://drive.google.com/drive/folders/17w3xHl4Qy1WrGA7JInzwUhUIlh20-7gh?usp=drive_link](https://drive.google.com/drive/folders/17w3xHl4Qy1WrGA7JInzwUhUIlh20-7gh?usp=drive_link)

## O que ele faz

Para cada questão do ENADE Computação:

1. Junta os dados da questão (enunciado, gabarito oficial, situação da
   questão) com a resposta que precisa ser avaliada.
2. Busca a imagem associada à questão, se houver.
3. Monta um prompt detalhado e envia tudo (texto + imagem) para o Mistral.
4. O Mistral avalia a resposta em 5 critérios objetivos e devolve, além
   disso, uma resolução técnica da questão.
5. O resultado é validado e salvo em `resultados.csv`.

O processo é executado questão por questão, salvando o progresso a cada
uma — se o script parar no meio (erro, rate limit, falta de energia), dá
pra rodar de novo sem perder o que já foi processado.

## Como funciona

### 1. Entrada de dados

Dois CSVs são lidos e cruzados pelo número da questão:

- `Enade2021-Questões.csv` — enunciado e demais dados da questão.
- `Enade2021-GabaritoFinal.csv` — gabarito oficial do INEP e situação
  oficial da questão (regular ou anulada).

A resposta que está sendo avaliada vem da coluna **"Gabarito comentado
final"** (o nome é uma herança do CSV original, mas é nela que está
armazenada a resposta a ser julgada).

Todo dado objetivo (enunciado, gabarito INEP, situação oficial, resposta
avaliada) é resolvido em Python **antes** de montar o prompt — o modelo
nunca precisa (nem deve) inferir ou adivinhar esses dados.

### 2. Prompt

O Mistral recebe:

- Enunciado da questão (+ imagem, quando existir).
- Gabarito INEP (única referência oficial para a alternativa correta).
- Situação oficial da questão (regular ou anulada).
- A resposta que deve ser avaliada.

E retorna um array JSON com 7 posições:

```json
[
  numero_da_questao,
  se_acertou,             // "SIM" ou "NAO"
  explicacao_ta_boa,      // "SIM" ou "NAO"
  sem_rastro_llm,         // "SIM" ou "NAO"
  acordo_com_inep,        // "SIM" ou "NAO"
  anulada_tem_explicacao, // "SIM", "NAO" ou null (se a questão não foi anulada)
  explicacao_final        // resolução técnica da questão (string)
]
```

Se todos os critérios aplicáveis forem "SIM", `explicacao_final` mantém a
resposta original. Se algum for "NAO", ela é substituída por uma
resolução técnica completa, escrita como se fosse de um professor
especialista.

### 3. Proteções contra alucinação

Além do prompt, o `main.py` aplica regras determinísticas **por cima** do
que o Mistral responde, para que erros do modelo não passem despercebidos:

- Sem resposta avaliada → `se_acertou`, `explicacao_ta_boa`,
  `sem_rastro_llm` e `acordo_com_inep` são forçados para `"NAO"`.
- Sem Gabarito INEP → `se_acertou` e `acordo_com_inep` forçados para
  `"NAO"`.
- `anulada_tem_explicacao` é `null` ou "aplicável" com base na situação
  oficial do gabarito (Python decide isso, não o modelo).

### 4. Retry e rate limit

Chamadas ao Mistral têm retry com backoff exponencial (6 tentativas,
começando em 15s e dobrando) para lidar com erros de rate limit (HTTP
429), além de uma pequena pausa fixa entre chamadas para reduzir a chance
de atingir o limite.

### 5. Parser

`parser.py` valida rigorosamente a resposta do Mistral: JSON válido,
array de exatamente 7 posições, tipos corretos, valores `SIM`/`NAO`
válidos, `null` só onde é permitido. Nenhuma resposta inválida é
"corrigida" silenciosamente — o erro é registrado e a próxima questão
segue normalmente.

### 6. Resume

Ao rodar de novo, o script lê o `resultados.csv` existente e pula
questões que já têm um resultado válido (com `se_acertou` preenchido e
sem `ERRO:` em `explicacao_final`). Questões que falharam antes são
reprocessadas automaticamente.

## Estrutura do projeto

```
main.py      # orquestra o pipeline (leitura, merge, resume, salvamento incremental)
prompt.py    # monta o prompt enviado ao Mistral
mistral.py   # chamada à API do Mistral, com retry/backoff
parser.py    # valida e faz o parsing da resposta do Mistral
images.py    # localiza a imagem associada a cada questão
```

## Como executar

1. Configure a variável de ambiente `MISTRAL_API_KEY` (num arquivo
   `.env`, por exemplo).
2. Garanta que os CSVs estejam em `../data/2021/` e as imagens em
   `../static/2021/`.
3. Rode:

```bash
python main.py
```

Os resultados são salvos incrementalmente em `../data/resultados.csv`,
codificados em `utf-8-sig`.