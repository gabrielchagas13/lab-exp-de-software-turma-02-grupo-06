"""
Kata 02 - Ranking de tags normalizadas. Ver kata.md para o enunciado completo.

Trial: guilherme (GL) | tratamento: manual | issue #40
"""

import re


def normalize_tags(tags: list[str]) -> list[tuple[str, int]]:
    # 1. Normalizar cada tag e contar a frequencia
    contagem: dict[str, int] = {}

    for tag in tags:
        # Remove espacos nas pontas e coloca em minusculo
        tag_formatada = tag.strip().lower()
        # Substitui qualquer sequencia de espacos ou hifens por um unico hifen
        tag_normalizada = re.sub(r"[\s-]+", "-", tag_formatada)

        if tag_normalizada not in contagem:
            contagem[tag_normalizada] = 0
        contagem[tag_normalizada] += 1

    # 2. Ordenar: maior frequencia primeiro; em empate, ordem alfabetica
    lista_tags = list(contagem.items())
    lista_tags.sort(key=lambda item: (-item[1], item[0]))

    # 3. Retornar as top 3 mais frequentes
    return lista_tags[:3]
