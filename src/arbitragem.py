import os
import re
import time
import random
import mimetypes
import pandas as pd
from dotenv import load_dotenv
from google import genai
from google.genai import types

from prompt_arbitragem import montar_prompt_arbitragem
from images import buscar_imagem

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)
MODEL = "gemini-3.6-flash"  # Ou o modelo exato que estiver configurado no seu gemini.py

# Arquivos de entrada e saída
ARQUIVO_RESPOSTAS_LLM = "../data/teste/Enade2021-RespostasLLMs.csv"
ARQUIVO_GABARITO_BRUTO = "../data/teste/Enade2021-GabaritoINEP.csv" 
ARQUIVO_QUESTOES = "../data/teste/Enade2021-Questões.csv"

ARQUIVO_SAIDA = "../data/teste/Enade2021-GabaritoFinal.csv" # Gerado e atualizado incrementalmente

MAX_TENTATIVAS = 5

def _mime_type_da_imagem(caminho_imagem: str) -> str:
    tipo, _ = mimetypes.guess_type(caminho_imagem)
    return tipo or "image/png"

def chamar_gemini_texto(prompt: str, caminho_imagem: str | None = None) -> str:
    config = types.GenerateContentConfig(
        temperature=0.2,
        response_mime_type="text/plain",
    )
    
    conteudo = [prompt]
    
    if caminho_imagem:
        with open(caminho_imagem, "rb") as arquivo:
            imagem_bytes = arquivo.read()
        
        conteudo.append(
            types.Part.from_bytes(
                data=imagem_bytes,
                mime_type=_mime_type_da_imagem(caminho_imagem),
            )
        )
    
    for tentativa in range(1, MAX_TENTATIVAS + 1):
        try:
            time.sleep(3)
            response = client.models.generate_content(
                model=MODEL,
                contents=conteudo,
                config=config,
            )
            return response.text
        except Exception as e:
            erro_str = str(e).lower()
            # ---> ADICIONADA A MODIFICAÇÃO DO ERRO 503 <---
            if "429" in erro_str or "quota" in erro_str or "503" in erro_str or "unavailable" in erro_str:
                espera = 15 * (2 ** (tentativa - 1))
                print(f"  Servidor ocupado ou Rate limit. Aguardando {espera}s...")
                time.sleep(espera)
            else:
                raise e
    raise Exception("Falha após múltiplas tentativas no Gemini.")

def extrair_campo(texto: str, regex_pattern: str) -> str:
    match = re.search(regex_pattern, texto, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""

def desanonimizar_modelo(resposta_recomendada: str, mapa_modelos: dict) -> str:
    if not resposta_recomendada or "NENHUMA" in resposta_recomendada.upper():
        return "Nenhum"
    
    modelos_finais = []
    if "A" in resposta_recomendada: modelos_finais.append(mapa_modelos["A"])
    if "B" in resposta_recomendada: modelos_finais.append(mapa_modelos["B"])
    if "C" in resposta_recomendada: modelos_finais.append(mapa_modelos["C"])
    
    return " + ".join(modelos_finais) if modelos_finais else "Desconhecido"


CAMPO_MINIMO_CARACTERES = 40


def construir_fallback_gabarito(
    resposta_recomendada: str,
    mapa_linha: dict,
    gabarito_oficial: str,
    numero_questao: int,
) -> str:
    """
    Fallback determinístico: usado quando o Gemini deixa o campo
    GABARITO COMENTADO FINAL vazio ou curto demais (o que costuma
    acontecer quando ele julga a resposta vencedora já adequada e
    "esquece" de copiá-la, em vez de escrever algo novo). Em vez de
    confiar que o modelo sempre vai obedecer a instrução de nunca
    deixar o campo vazio, o Python garante isso montando o texto a
    partir da(s) resposta(s) originais da(s) letra(s) vencedora(s).

    Não é tão bem escrito quanto uma síntese feita pelo modelo quando
    há mais de uma letra envolvida, mas nunca fica vazio.
    """

    letras = [letra for letra in ["A", "B", "C"] if letra in resposta_recomendada.upper()]

    if not letras:
        return ""

    def montar_texto_resposta(linha):
        alt = str(linha.get("Alternativa", ""))
        just = str(linha.get("Justificativa da resposta", ""))
        analise = str(linha.get("Análise das alternativas", ""))
        return f"Alternativa escolhida: {alt}\n\n{just}\n\n{analise}"

    partes = [montar_texto_resposta(mapa_linha[letra]) for letra in letras]
    corpo = "\n\n---\n\n".join(partes)

    return f"QUESTÃO {numero_questao} — Alternativa {gabarito_oficial}\n\n{corpo}"

def carregar_resultados_existentes(caminho):
    """Carrega o CSV de saída se já existir para permitir retomar de onde parou."""
    if os.path.exists(caminho):
        try:
            return pd.read_csv(caminho, encoding="utf-8-sig").to_dict("records")
        except Exception:
            pass
    return []

def main():
    print("Iniciando arbitragem das respostas...")
    
    # 1. Carregar bases de entrada
    df_llms = pd.read_csv(ARQUIVO_RESPOSTAS_LLM)
    df_gabarito = pd.read_csv(ARQUIVO_GABARITO_BRUTO)
    df_questoes = pd.read_csv(ARQUIVO_QUESTOES)

    df_llms["numero_da_questao"] = df_llms["Questão"].astype(str).str.extract(r"(\d+)")[0].astype(int)
    df_gabarito["numero_da_questao"] = df_gabarito["Questão"].astype(str).str.extract(r"(\d+)")[0].astype(int)
    df_questoes["numero_da_questao"] = df_questoes["Questão"].astype(str).str.extract(r"(\d+)")[0].astype(int)
    
    mapa_gabaritos = df_gabarito.set_index("numero_da_questao")["Gabarito INEP"].to_dict()
    mapa_enunciados = df_questoes.set_index("numero_da_questao")["Enunciado"].to_dict()

    questoes_agrupadas = df_llms.groupby("numero_da_questao")
    
    # ---> NOVO: Carregar resultados parciais e mapear o que já está pronto <---
    resultados = carregar_resultados_existentes(ARQUIVO_SAIDA)
    questoes_concluidas = set()
    for r in resultados:
        if "Questão " in r and str(r.get("Modelo(s)-base")) != "ERRO":
            questoes_concluidas.add(int(str(r["Questão "]).strip()))

    for numero_questao, grupo in questoes_agrupadas:
        # Pular se já foi processada com sucesso em uma rodada anterior
        if numero_questao in questoes_concluidas:
            print(f"Questão {numero_questao} já arbitrada anteriormente. Pulando.")
            continue

        print(f"Arbitrando questão {numero_questao}...")
        
        linhas = grupo.to_dict("records")
        if len(linhas) != 3:
            print(f"  Aviso: Questão {numero_questao} possui {len(linhas)} resposta(s) (esperado 3). Pulando.")
            continue
            
        gabarito_oficial = mapa_gabaritos.get(numero_questao, "[Não Informado]")
        enunciado = mapa_enunciados.get(numero_questao, "[Não Informado]")

        # 2. Anonimizar LLMs
        random.shuffle(linhas)
        mapa_modelos = {
            "A": linhas[0]["Modelo"],
            "B": linhas[1]["Modelo"],
            "C": linhas[2]["Modelo"]
        }
        mapa_linha = {
            "A": linhas[0],
            "B": linhas[1],
            "C": linhas[2],
        }
        
        def montar_texto_resposta(linha):
            alt = str(linha.get("Alternativa", ""))
            just = str(linha.get("Justificativa da resposta", ""))
            analise = str(linha.get("Análise das alternativas", ""))
            return f"Alternativa escolhida: {alt}\n\n{just}\n\n{analise}"

        dados_prompt = {
            "numero_questao": numero_questao,
            "enunciado": enunciado,
            "gabarito_oficial": gabarito_oficial,
            "resposta_a": montar_texto_resposta(linhas[0]),
            "resposta_b": montar_texto_resposta(linhas[1]),
            "resposta_c": montar_texto_resposta(linhas[2])
        }

        prompt = montar_prompt_arbitragem(dados_prompt)
        
        imagem = buscar_imagem(numero_questao)
        if imagem:
            print(f"  Imagem encontrada: {imagem}")
        
        # 3. Processamento
        novo_resultado = {}
        try:
            resposta_gemini = chamar_gemini_texto(prompt, caminho_imagem=imagem)
            
            revisao_humana = extrair_campo(resposta_gemini, r"REVISÃO HUMANA RECOMENDADA:\s*(Sim|Não|Nao)")
            status = "Em revisão" if revisao_humana.lower() == "sim" else "Finalizado"
            
            resposta_recomendada = extrair_campo(resposta_gemini, r"RESPOSTA-BASE RECOMENDADA:\s*(.*?)(?=\nREVISÃO|\Z)")
            modelos_base = desanonimizar_modelo(resposta_recomendada, mapa_modelos)
            
            gabarito_comentado = extrair_campo(resposta_gemini, r"GABARITO COMENTADO FINAL:\s*(.*)").strip()

            # Nunca aceita o campo vazio/curto demais quando existe uma
            # resposta-base recomendada — o Gemini às vezes "esquece"
            # de copiar a resposta vencedora quando ela já está boa.
            # Ver construir_fallback_gabarito() para o motivo.
            if (
                "NENHUMA" not in resposta_recomendada.upper()
                and len(gabarito_comentado) < CAMPO_MINIMO_CARACTERES
            ):
                print(
                    "  Aviso: GABARITO COMENTADO FINAL veio vazio/curto "
                    "demais — usando o texto original da resposta "
                    "vencedora como fallback."
                )
                gabarito_comentado = construir_fallback_gabarito(
                    resposta_recomendada,
                    mapa_linha,
                    gabarito_oficial,
                    numero_questao,
                )

            novo_resultado = {
                "Questão ": numero_questao,
                "Gabarito INEP": gabarito_oficial,
                "Modelo(s)-base": modelos_base,
                "Gabarito comentado final": gabarito_comentado.strip(),
                "Status": status
            }
            
            print(f"  ✓ Arbitrada (Modelos-base: {modelos_base} | Status: {status})")
            
        except Exception as e:
            print(f"  ✗ Erro ao arbitrar questão {numero_questao}: {e}")
            novo_resultado = {
                "Questão ": numero_questao,
                "Gabarito INEP": gabarito_oficial,
                "Modelo(s)-base": "ERRO",
                "Gabarito comentado final": "",
                "Status": "Em revisão"
            }

        # ---> NOVO: Atualizar lista e salvar no CSV imediatamente <---
        # Remove tentativas falhas anteriores desta mesma questão, se houver
        resultados = [r for r in resultados if str(r.get("Questão ")).strip() != str(numero_questao)]
        resultados.append(novo_resultado)
        
        # Salva o arquivo sobrescrevendo com a lista atualizada
        df_final = pd.DataFrame(resultados)
        df_final.to_csv(ARQUIVO_SAIDA, index=False, encoding="utf-8-sig")

    print(f"\nProcessamento concluído! O ficheiro completo encontra-se em: {ARQUIVO_SAIDA}")

if __name__ == "__main__":
    main()