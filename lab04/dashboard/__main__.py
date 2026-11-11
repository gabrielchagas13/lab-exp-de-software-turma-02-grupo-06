"""Gera o dashboard do Lab04 em um único HTML (issue #78).

Reaproveita `simulacao.executar`, então o conjunto simulado e os testes do
dashboard são exatamente os de `python -m simulacao` com a mesma semente.

Uso:
    python -m dashboard --config config.json
    python -m dashboard --config config.json --saida /tmp/teste.html
"""
import argparse
import json
import os
import sys

from dashboard import pagina
from dashboard.distribuicoes import nulas
import sim
from dashboard.graficos import g1_histogramas, g2_nula, g3_erro_tipo1, g_violacoes
from simulacao import cenario as cen
from simulacao.__main__ import executar
from simulacao.conclusao import avaliar, resumo
from simulacao.experimentos import REPETICOES, erro_tipo1, poder


def gerar(config_path, saida=None):
    """Monta o HTML e grava em `saida` (padrão: `dashboard.saida` do config)."""
    with open(config_path, encoding="utf-8") as f:
        cfg = json.load(f)
    opcoes = cfg.get("dashboard", {})

    c, controle, tratamento, resultados, _, raiz = executar(config_path)
    reais = cen.carregar_reais(os.path.join(raiz, cfg["coleta"]["saida"]))
    simulados = {cen.GRUPO_CONTROLE: controle, cen.GRUPO_TRATAMENTO: tratamento}
    curvas = nulas(tratamento, controle, c["alfa"])
    # Q1 (#79): mesma semente do resto da página, para o HTML ser reproduzível.
    erros = erro_tipo1(c, repeticoes=opcoes.get("repeticoes", REPETICOES),
                       semente=cfg["seed"])

    # Conclusão (#84): o que ainda não foi rodado entra como pendente, em vez
    # de a página concluir a partir de dados que não tem.
    taxas_poder = poder(c, repeticoes=opcoes.get("repeticoes", REPETICOES),
                        semente=cfg["seed"])
    avaliacoes = avaliar(c, erros_tipo1=erros,
                         poder={k: t.taxa for k, t in taxas_poder.items()})
    # Q3 (#81) e dados reais (#82): módulo `sim`, mesma semente.
    violacoes = sim.simular_tudo(reps=opcoes.get("repeticoes", REPETICOES),
                                 seed=cfg["seed"])

    links = [("Repositório", opcoes.get("repo_url")),
             ("GitHub Projects", opcoes.get("projects_url")),
             ("Dashboard publicado", opcoes.get("pages_url"))]
    html = pagina.montar(c, resultados, curvas,
                         g1_histogramas(reais, simulados, c),
                         g2_nula(curvas, resultados, c["alfa"]),
                         links, cfg["seed"],
                         erros_tipo1=erros,
                         fig_g3=g3_erro_tipo1(erros, c["alfa"]),
                         avaliacoes=avaliacoes, contagem=resumo(avaliacoes),
                         violacoes=violacoes,
                         fig_violacoes=g_violacoes(violacoes, c["alfa"]),
                         reais=sim.testes_reais(sim.carregar_reais(
                             os.path.join(raiz, cfg["coleta"]["saida"]))).to_dict("records"))

    destino = saida or os.path.join(raiz, opcoes.get("saida", "dashboard/index.html"))
    os.makedirs(os.path.dirname(os.path.abspath(destino)), exist_ok=True)
    with open(destino, "w", encoding="utf-8") as f:
        f.write(html)
    return destino


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(prog="dashboard", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--saida", default=None, help="caminho do HTML gerado")
    args = parser.parse_args(argv)
    print(f"Dashboard gravado em {gerar(args.config, args.saida)}")


if __name__ == "__main__":
    main()
