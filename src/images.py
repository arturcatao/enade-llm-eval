from pathlib import Path


PASTA_IMAGENS = Path("static/2021")


def buscar_imagem(numero_questao: int) -> str | None:
    """
    Procura a imagem correspondente à questão.

    Exemplo:
        questão 12 -> static/questoes/12.png

    Retorna:
        caminho da imagem se existir
        None caso contrário
    """

    extensoes = [".png", ".jpg", ".jpeg", ".webp"]

    for extensao in extensoes:
        caminho = PASTA_IMAGENS / f"{numero_questao}{extensao}"

        if caminho.exists():
            return str(caminho)

    return None