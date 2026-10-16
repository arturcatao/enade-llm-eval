# ENADE LLM Eval — avaliação e arbitragem de respostas do ENADE com LLMs

Repositório com dois pipelines em Python que usam modelos de linguagem
com visão para trabalhar com questões objetivas de provas do ENADE
(Computação), de qualquer ano letivo:

1. **Avaliação de respostas** (`src/main.py`) — julga respostas geradas
   para as questões de uma prova comparando-as com o gabarito oficial
   do INEP.
2. **Arbitragem de respostas** (`src/arbitragem.py`) — compara respostas
   produzidas por diferentes LLMs para a mesma questão, escolhe a melhor
   base e monta o gabarito comentado final.

Os caminhos de entrada e saída (ano da prova, nomes dos CSVs, pasta de
imagens) são configurados pelas constantes no topo de cada script, então
o mesmo código serve para qualquer edição da prova — basta apontar para
a pasta do ano desejado.

Resultados completos da avaliação estão disponíveis neste link:

[https://drive.google.com/drive/folders/17w3xHl4Qy1WrGA7JInzwUhUIlh20-7gh?usp=drive_link](https://drive.google.com/drive/folders/17w3xHl4Qy1WrGA7JInzwUhUIlh20-7gh?usp=drive_link)

Colab auxiliar:

[https://colab.research.google.com/drive/1RPQm8IinuGui3r3PnkvMzeBzQhFD08A4?usp=sharing](https://colab.research.google.com/drive/1RPQm8IinuGui3r3PnkvMzeBzQhFD08A4?usp=sharing)

---

## 1. Pipeline de avaliação

Para cada questão da prova:

1. Junta os dados da questão (enunciado, gabarito oficial, situação da
   questão) com a resposta que precisa ser avaliada.
2. Busca a imagem associada à questão, se houver.
3. Monta um prompt detalhado e envia tudo (texto + imagem) para o
   Gemini.
4. O modelo avalia a resposta em 5 critérios objetivos e devolve, além
   disso, uma resolução técnica da questão.
5. O resultado é validado, passa pelas regras determinísticas e é salvo
   em `resultados.csv`.

O processo é executado questão por questão, salvando o progresso a cada
uma — se o script parar no meio (erro, rate limit, falta de energia),
dá pra rodar de novo sem perder o que já foi processado.

### 1.1 Entrada de dados

Dois CSVs são lidos e cruzados pelo número da questão (caminhos
configurados por `ARQUIVO_QUESTOES` e `ARQUIVO_GABARITO`, no topo do
`main.py`):

- **CSV de questões** — enunciado e demais dados da questão.
- **CSV de gabarito** — gabarito oficial do INEP e situação oficial da
  questão (regular ou anulada).

Ou seja: uma prova nova entra como uma nova pasta em `data/<ano>/` com
esses dois arquivos, sem mudar código — só os caminhos.

Colunas esperadas (nomes usados pelos CSVs do ENADE):

- `Questão ` — identificador da questão (o número é extraído por
  regex, então variações como "Questão 12 — Computação" funcionam).
- `Enunciado` — texto da questão.
- `Gabarito INEP` — alternativa oficial correta.
- `Situação` — situação oficial (ex.: regular, anulada).
- `Gabarito comentado final` — a resposta que será avaliada.

A resposta que está sendo avaliada vem da coluna **"Gabarito comentado
final"** (o nome é uma herança do CSV original, mas é nela que está
armazenada a resposta a ser julgada).

Todo dado objetivo (enunciado, gabarito INEP, situação oficial, resposta
avaliada) é resolvido em Python **antes** de montar o prompt — o modelo
nunca precisa (nem deve) inferir ou adivinhar esses dados. Quando há
colunas homônimas nos dois CSVs, o merge as renomeia com sufixos
`_questao`/`_gabarito` e o script tenta os nomes nas duas variantes.

### 1.2 Prompt

O modelo recebe:

- Enunciado da questão (+ imagem, quando existir).
- Gabarito INEP (única referência oficial para a alternativa correta).
- Situação oficial da questão (regular ou anulada).
- A resposta que deve ser avaliada.

E retorna um objeto JSON com 7 campos nomeados, que é convertido para
uma lista de 7 posições antes do parsing:

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

Se todos os critérios aplicáveis forem "SIM", `explicacao_final` mantém
a resposta original. Se algum for "NAO", ela é substituída por uma
resolução técnica completa, escrita como se fosse de um professor
especialista.

Quando a situação oficial da questão é **"Anulada"**, o prompt recebe um
bloco de regra com precedência máxima: `explicacao_final` deve ser
exatamente a string `QUESTÃO ANULADA`, sem cabeçalho, sem análise das
alternativas e sem justificativa da anulação — as demais regras de
`explicacao_final` são ignoradas nesse caso, e os demais campos continuam
sendo avaliados normalmente. A checagem de anulação é feita em Python
(função `questao_esta_anulada`), de modo que o valor também pode ser
forçado do lado do script, sem depender da obediência do modelo.

### 1.3 Proteções contra alucinação

Além do prompt, o `main.py` aplica regras determinísticas **por cima** do
que o modelo responde, para que erros do modelo não passem despercebidos:

- Sem resposta avaliada → `se_acertou`, `explicacao_ta_boa`,
  `sem_rastro_llm` e `acordo_com_inep` são forçados para `"NAO"`.
- Sem Gabarito INEP → `se_acertou` e `acordo_com_inep` forçados para
  `"NAO"`.
- `anulada_tem_explicacao` é `null` ou "aplicável" com base na situação
  oficial do gabarito (Python decide isso, não o modelo).

### 1.4 Chamada ao modelo

A avaliação usa o **Gemini** (`src/gemini.py`, modelo
`gemini-3.6-flash`), com chave `GEMINI_API_KEY` carregada do `.env`:

- `temperature=0.0` e `response_mime_type=application/json` com
  `response_schema`, para obter a saída estruturada.
- Como o schema do Gemini é um subconjunto do OpenAPI 3.0 e não aceita
  tupla heterogênea, pede-se um **objeto com 7 campos nomeados** que é
  convertido para a mesma lista de 7 posições que o `parser.py` espera —
  assim `main.py` e `parser.py` funcionam igual para qualquer cliente.
- Imagem enviada em binário via `Part.from_bytes`, com MIME type deduzido
  do arquivo.
- Retry com backoff exponencial (6 tentativas, começando em 15s,
  dobrando até no máximo 300s) para erros de rate limit (HTTP 429,
  `resource_exhausted`, cota), além de uma pausa fixa de 3s antes de
  cada chamada para reduzir a chance de atingir o limite.

Existe também `src/mistral.py`, um cliente equivalente para o Mistral
(mesmo formato de saída e mesma estratégia de retry), que pode ser
alternado no `main.py` trocando o import de `avaliar`.

### 1.5 Parser

`src/parser.py` valida rigorosamente a resposta: JSON válido, array de
exatamente 7 posições, tipos corretos, valores `SIM`/`NAO` válidos,
`null` só onde é permitido. Nenhuma resposta inválida é "corrigida"
silenciosamente — o erro é registrado e a próxima questão segue
normalmente.

### 1.6 Saída e resume

O resultado de cada questão é gravado em `resultados.csv` (caminho
configurado por `ARQUIVO_SAIDA`), com as colunas `numero_da_questao`,
`se_acertou`, `explicacao_ta_boa`, `sem_rastro_llm`, `acordo_com_inep`,
`anulada_tem_explicacao` e `explicacao_final`.

Ao rodar de novo, o script lê o `resultados.csv` existente e pula
questões que já têm um resultado válido (com `se_acertou` preenchido e
sem `ERRO:` em `explicacao_final`). Questões que falharam antes são
reprocessadas automaticamente. Para rodar uma prova diferente, basta
apontar `ARQUIVO_SAIDA` para outro arquivo — assim uma execução nunca
sobrescreve a outra.

---

## 2. Pipeline de arbitragem

`src/arbitragem.py` resolve outra etapa do projeto: a partir de
respostas já geradas por LLMs para a mesma questão, decidir qual (ou
qual combinação) serve de base para o gabarito comentado.

Entradas (caminhos configurados no topo do `arbitragem.py`):

- **CSV de respostas LLM** — uma linha por (questão, modelo), com as
  colunas `Questão`, `Modelo`, `Alternativa`, `Justificativa da
  resposta` e `Análise das alternativas`. Cada questão deve ter
  exatamente 3 respostas (uma de cada modelo).
- **CSV de gabarito INEP** — colunas `Questão` e `Gabarito INEP`.
- **CSV de questões** — colunas `Questão` e `Enunciado`.

Saída (`ARQUIVO_SAIDA`): um CSV com as colunas `Questão `, `Gabarito
INEP`, `Modelo(s)-base`, `Gabarito comentado final` e `Status`.

Fluxo, por questão:

1. As três respostas são **anonimizadas**: a ordem é embaralhada e elas
   viram Resposta A, B e C, de modo que o avaliador não saiba qual
   modelo escreveu o quê. Ao final, os nomes reais dos modelos são
   devolvidos (`Modelo(s)-base`).
2. O prompt de arbitragem (`src/prompt_arbitragem.py`) recebe enunciado,
   gabarito oficial e as três respostas, e envia tudo (texto + imagem)
   para o Gemini (`temperature=0.2`, saída em texto puro).
3. O modelo pontua cada resposta de 0 a 5 em seis critérios — correção
   conceitual, coerência lógica, fundamentação, análise dos
   distratores, clareza pedagógica e aderência ao enunciado (total 30) —
   e indica quais são elegíveis, a resposta-base recomendada (letra,
   síntese de letras ou NENHUMA), se há empate técnico e se recomenda
   **revisão humana**.
4. Os campos são extraídos por regex (`RESPOSTA-BASE RECOMENDADA`,
   `REVISÃO HUMANA RECOMENDADA`, `GABARITO COMENTADO FINAL`) e o `Status`
   da questão fica `"Finalizado"` ou `"Em revisão"`.
5. O resultado é gravado no CSV imediatamente, questão a questão.

O prompt impõe que o avaliador use **apenas** o enunciado, o gabarito
oficial e as três respostas: proíbe busca na internet e identificação
dos modelos; não escolhe uma resposta só porque ela coincide com o
gabarito; marca como não elegível qualquer resposta cuja alternativa
diverga do INEP (ainda que ela seja bem escrita); permite declarar
empate técnico; e, diante de inconsistência relevante entre enunciado e
gabarito, recomenda revisão humana sem substituir o gabarito
unilateralmente.

O campo `GABARITO COMENTADO FINAL` segue duas regras: se a resposta
vencedora já estiver tecnicamente correta e bem fundamentada, o texto
dela é copiado na íntegra (com o cabeçalho `QUESTÃO <n> — Alternativa
<Letra>`); se houver problema relevante ou síntese de mais de uma
resposta, é escrita uma resolução técnica nova. Quando o modelo devolve
esse campo vazio ou curto demais — o que acontece quando ele julga a
resposta vencedora já adequada e "esquece" de copiá-la — o Python monta
o texto a partir da(s) resposta(s) original(is) da(s) letra(s)
vencedora(s), garantindo que o campo nunca fique vazio.

A arbitragem também roda com salvamento incremental: questões já
arbitradas com sucesso são puladas e as que terminaram com erro
(`Modelo(s)-base = ERRO`) são reprocessadas na próxima execução. As
chamadas aguardam 15 segundos fixos em caso de rate limit/cota/erro de
servidor e repetem até dar certo.

O gabarito comentado gerado aqui é exatamente o formato que o pipeline
de avaliação consome na coluna "Gabarito comentado final" — ou seja, a
arbitragem produz a entrada da avaliação.

---

## 3. Estrutura do projeto

```
src/
  main.py               # orquestra a avaliação (leitura, merge, resume, salvamento incremental)
  prompt.py             # prompt de avaliação e regra de questão anulada
  gemini.py             # cliente Gemini (usado pelo main.py)
  mistral.py            # cliente Mistral (alternativa ao Gemini)
  parser.py             # valida e faz o parsing da resposta do modelo
  images.py             # localiza a imagem associada a cada questão
  arbitragem.py         # pipeline de arbitragem das respostas
  prompt_arbitragem.py  # prompt da avaliação comparativa A/B/C
data/                   # uma pasta por ano/prova, com os CSVs (gitignored)
static/                 # uma pasta por ano/prova, com as imagens (gitignored)
requirements.txt
.env                    # GEMINI_API_KEY / MISTRAL_API_KEY (gitignored)
```

Organização sugerida dos dados — uma pasta por edição da prova:

```
data/<ano>/
  Enade<ano>-Questões.csv
  Enade<ano>-GabaritoFinal.csv
  Enade<ano>-RespostasLLM.csv
  Enade<ano>-Gabarito_INEP.csv
static/<ano>/
  1.png, 2.png, ...     # imagem de cada questão (opcional)
```

---

## 4. Como executar

1. Crie o ambiente e instale as dependências:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   pip install google-genai
   ```

2. Configure as chaves num arquivo `.env`:

   ```
   GEMINI_API_KEY=...
   MISTRAL_API_KEY=...
   ```

3. Coloque os CSVs da prova que você quer processar em `data/<ano>/` e
   as imagens em `static/<ano>/`. Em seguida, ajuste no topo dos
   scripts os caminhos para essa pasta:

   - `src/main.py` — `ARQUIVO_QUESTOES`, `ARQUIVO_GABARITO`,
     `ARQUIVO_SAIDA`.
   - `src/arbitragem.py` — `ARQUIVO_RESPOSTAS_LLM`,
     `ARQUIVO_GABARITO_BRUTO`, `ARQUIVO_QUESTOES`, `ARQUIVO_SAIDA`.
   - `src/images.py` — `PASTA_IMAGENS` (pasta das imagens do ano).

4. Rode a partir de `src/`:

   ```bash
   cd src
   python main.py        # avaliação    → data/<ano>/resultados.csv
   python arbitragem.py  # arbitragem   → data/<ano>/GabaritoFinal.csv
   ```

Os resultados são salvos incrementalmente, em `utf-8-sig` (abrem
direto no Excel). Como o arquivo de saída é configurável, dá para
rodar várias provas em paralelo, cada uma com o seu CSV de resultados.
