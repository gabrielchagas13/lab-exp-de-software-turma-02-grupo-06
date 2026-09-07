# Kata 04 — Agrupamento de anagramas

Implemente `anagram_clusters(words)` que agrupa palavras que são anagramas umas das outras (mesmas letras, quantidades iguais, em qualquer ordem).

1. Cada grupo deve ser uma lista de palavras ordenada alfabeticamente.
2. A lista de grupos deve ser ordenada por **tamanho do grupo decrescente**; em caso de empate, pela **primeira palavra do grupo (alfabética)**.
3. Palavras sem nenhum anagrama na lista formam um grupo de tamanho 1.

**Assinatura:**
```python
def anagram_clusters(words: list[str]) -> list[list[str]]:
    ...
```

**Exemplo:** `["ola", "lao", "gato", "toga"]` → `[["gato", "toga"], ["lao", "ola"]]`

**Restrições:** todas as palavras são minúsculas, apenas letras (sem acentos ou espaços).
