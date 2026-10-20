"""Validação das planilhas de rótulos de um avaliador (issues #63, #64, #65).

Confere, antes de entregar os rótulos para o kappa (`validacao.concordancia`):

- as colunas são exatamente as que `validacao.amostra` gerou (ninguém apagou,
  renomeou ou acrescentou coluna);
- os itens são os da amostra sorteada (`amostra.json`), sem faltar, sobrar nem
  repetir; uma linha a mais ou a menos desalinharia o kappa;
- cada rótulo preenchido é um dos valores aceitos (`Sim`, `sim ` ou `s` viram
  uma categoria extra no kappa e derrubam a concordância sem motivo real).

Rótulos em branco não são erro, são pendência: a planilha pode ser validada
enquanto ainda está sendo preenchida. Com `--completo`, pendência também falha.

Uso:
    python -m validacao.validar_rotulos --avaliador gl [--completo]
"""
import argparse
import csv
import json
import os

from validacao.amostra import AVALIADORES, COLUNAS_RELEASES, COLUNAS_REPOS, OPCOES

VALORES = {coluna: set(opcoes.split(" | ")) for coluna, opcoes in OPCOES.items()}

NIVEIS = (
    ("repos", COLUNAS_REPOS, ("full_name",), ("tipo_projeto", "releases_sao_entregas")),
    ("releases", COLUNAS_RELEASES, ("full_name", "tag"), ("corretiva",)),
)


def _ler(caminho):
    with open(caminho, encoding="utf-8", newline="") as f:
        leitor = csv.DictReader(f)
        return leitor.fieldnames or [], list(leitor)


def validar_planilha(caminho, colunas, chave, rotulos, amostra, n_esperado):
    """Valida uma planilha. Retorna (erros, pendencias), listas de mensagens."""
    if not os.path.isfile(caminho):
        return [f"arquivo não encontrado: {caminho}"], []
    cabecalho, linhas = _ler(caminho)
    nome = os.path.basename(caminho)
    if cabecalho != colunas:
        return [f"{nome}: colunas {cabecalho}, esperado {colunas}"], []

    erros, pendencias = [], []
    repos_amostra = set(amostra["repos"])
    vistos = set()
    for n, linha in enumerate(linhas, start=2):   # linha 1 é o cabeçalho
        item = tuple(linha[c] for c in chave)
        rotulo_item = "/".join(item)
        if item in vistos:
            erros.append(f"{nome}:{n}: item repetido {rotulo_item}")
        vistos.add(item)
        if linha["full_name"] not in repos_amostra:
            erros.append(f"{nome}:{n}: {linha['full_name']} não está na amostra sorteada")
        for coluna in rotulos:
            valor = linha[coluna]
            if valor == "":
                pendencias.append(f"{nome}:{n}: {rotulo_item} sem {coluna}")
            elif valor not in VALORES[coluna]:
                erros.append(f"{nome}:{n}: {coluna}={valor!r} inválido em {rotulo_item}; "
                             f"use {OPCOES[coluna]}")
    faltando = repos_amostra - {linha["full_name"] for linha in linhas}
    if faltando:
        erros.append(f"{nome}: faltam repositórios da amostra: {', '.join(sorted(faltando))}")
    if len(linhas) != n_esperado:
        erros.append(f"{nome}: {len(linhas)} itens, a amostra tem {n_esperado}")
    return erros, pendencias


def validar(dir_val, avaliador):
    """Valida as duas planilhas do avaliador. Retorna (erros, pendencias)."""
    with open(os.path.join(dir_val, "amostra.json"), encoding="utf-8") as f:
        amostra = json.load(f)
    esperado = {"repos": len(amostra["repos"]), "releases": amostra["n_releases_total"]}

    erros, pendencias = [], []
    for nivel, colunas, chave, rotulos in NIVEIS:
        caminho = os.path.join(dir_val, f"rotulos_{nivel}_{avaliador}.csv")
        e, p = validar_planilha(caminho, colunas, chave, rotulos, amostra, esperado[nivel])
        erros += e
        pendencias += p
    return erros, pendencias


def main(argv=None):
    parser = argparse.ArgumentParser(prog="validacao.validar_rotulos", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--avaliador", required=True, choices=AVALIADORES)
    parser.add_argument("--completo", action="store_true",
                        help="falha também se houver rótulo em branco")
    args = parser.parse_args(argv)
    with open(args.config, encoding="utf-8") as f:
        dir_val = os.path.join(json.load(f)["data_dir"], "validacao")

    erros, pendencias = validar(dir_val, args.avaliador)
    for msg in erros:
        print(f"ERRO      {msg}")
    for msg in pendencias[:20]:
        print(f"pendente  {msg}")
    if len(pendencias) > 20:
        print(f"pendente  ... e mais {len(pendencias) - 20}")
    print(f"\n{len(erros)} erro(s), {len(pendencias)} rótulo(s) em branco.")
    if erros or (args.completo and pendencias):
        raise SystemExit(1)
    print("Planilhas válidas." if not pendencias else "Sem erros; falta terminar de rotular.")


if __name__ == "__main__":
    main()
