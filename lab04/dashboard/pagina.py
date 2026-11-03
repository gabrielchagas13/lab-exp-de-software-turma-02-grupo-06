"""Montagem do HTML do dashboard (issue #78).

A página segue as sete seções do enunciado. Esta sprint preenche as seções 1
(cenário + G1) e 2 (estatística sob H0 + G2); as demais ficam como esqueleto,
cada uma apontando para a issue que vai preenchê-la, para que quem pegar a
issue só precise trocar o `pendente(...)` pelo conteúdo.

Os ids das divs dos gráficos são fixos: assim rodar o comando duas vezes com a
mesma semente gera um HTML idêntico, e o diff no git mostra só o que mudou.
"""
import html
import re

from dashboard.graficos import CORES_TESTE, NOMES_GRUPO, NOMES_TESTE, num, p_texto


def esc(texto):
    return html.escape(str(texto))


def markdown_simples(texto):
    """Converte o `**negrito**` e o `*itálico*` dos textos do cenário em HTML."""
    texto = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", esc(texto))
    return re.sub(r"\*(.+?)\*", r"<em>\1</em>", texto)


def tabela(cabecalho, linhas):
    th = "".join(f"<th>{esc(c)}</th>" for c in cabecalho)
    trs = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in linha) + "</tr>"
                  for linha in linhas)
    return f'<div class="tabela"><table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>'


def grafico(fig, div_id, incluir_js):
    return fig.to_html(full_html=False, include_plotlyjs="cdn" if incluir_js else False,
                       div_id=div_id, config={"displaylogo": False, "responsive": True})


def pendente(repo, issue, texto):
    return (f'<p class="pendente">Em construção: {esc(texto)} '
            f'(issue <a href="{esc(repo)}/issues/{issue}">#{issue}</a>).</p>')


def secao(numero, ancora, titulo, corpo):
    return (f'<section id="{ancora}"><h2><span class="num">{numero}</span> {esc(titulo)}</h2>'
            f"{corpo}</section>")


def _links(links):
    itens = []
    for rotulo, url in links:
        if url:
            itens.append(f'<a href="{esc(url)}">{esc(rotulo)}</a>')
        else:
            itens.append(f'<span class="sem-link" title="link ainda não configurado em '
                         f'config.json">{esc(rotulo)} (pendente)</span>')
    return " · ".join(itens)


def _legenda_cores():
    return " ".join(
        f'<span class="chip"><i style="background:{CORES_TESTE[k]}"></i>{esc(NOMES_TESTE[k])}</span>'
        for k in ("welch", "mannwhitney"))


def secao_cenario(c, fig_g1):
    hip = tabela(["Teste", "Compara", "H0", "H1"], [
        (esc(NOMES_TESTE[k]), esc(h["compara"]), esc(h["h0"]), esc(h["h1"]))
        for k, h in c["hipoteses"].items()])
    desc = tabela(
        ["Grupo", "n", "Mediana (h)", "Média (h)", "Máx. (h)", "Assimetria",
         "Assimetria do log", "Shapiro p (log)"],
        [(esc(NOMES_GRUPO[g]), d["n"], num(d["mediana"]), num(d["media"]),
          num(d["max"], 1), num(d["assimetria"]), num(d["assimetria_log"]),
          num(d["shapiro_log_p"], 3))
         for g, d in c["descritivas"].items()])
    params = tabela(["Parâmetro", "Valor"], [
        ("μ (log) do controle", num(c["mu_controle"], 3)),
        ("σ (log) comum aos grupos", num(c["sigma_comum"], 3)),
        ("Efeito simulado (log)", f'{num(c["efeito_observado_log"], 3)} '
                                  f'(mediana × {num(c["razao_medianas_observada"])})'),
        ("n por grupo", c["n_por_grupo"]),
        ("α", num(c["alfa"])),
    ])
    return secao(1, "cenario", "Cenário e dados", f"""
<p class="pergunta">{esc(c["pergunta"])}</p>
<h3>Hipóteses (uma por teste: eles não testam a mesma coisa)</h3>
{hip}
<p>{markdown_simples(c["bicaudal"])}</p>
<h3>Dados reais e parâmetros do gerador</h3>
<div class="lado-a-lado">{desc}{params}</div>
<h3>G1: dados reais × simulados</h3>
<p class="legenda-grafico">Histograma do tempo até o merge em cada grupo: os 30 PRs
coletados (cinza) e um conjunto de 30 gerado pela lognormal (verde), com a curva do
modelo tracejada. O botão <em>Horas</em> troca para a escala linear.</p>
{fig_g1}
<div class="previsao"><strong>Previsão registrada antes das simulações:</strong>
{markdown_simples(c["previsao"])}</div>
""")


def secao_nula(resultados, alfa, nulas, fig_g2):
    linhas = [(f'<span class="chip"><i style="background:{CORES_TESTE[k]}"></i>'
               f"{esc(r.teste)}</span>",
               num(r.estatistica, 3), p_texto(r.p_valor),
               f"{num(r.efeito, 3)} ({esc(r.efeito_nome)}, {esc(r.efeito_interpretacao)})",
               "sim" if r.rejeita_h0 else "não",
               esc(nulas[k].descricao))
              for k, r in resultados.items()]
    tab = tabela(["Teste", "Estatística", "p-valor", "Tamanho de efeito",
                  f"Rejeita H0 (α = {num(alfa)})", "Distribuição sob H0"], linhas)
    return secao(2, "nula", "Estatística sob H0 e p-valor do exemplo", f"""
<p class="legenda-grafico">Os dois testes aplicados ao conjunto simulado do G1.
Cada painel mostra a distribuição da estatística quando H0 é verdadeira: a faixa
sólida é a região de rejeição a {num(alfa * 100, 0)}% (as duas caudas, pois o teste
é bicaudal) e a área hachurada é o p-valor, ou seja, a probabilidade de uma
estatística pelo menos tão extrema quanto a observada se H0 fosse verdadeira.</p>
{fig_g2}
{tab}
""")


def montar(c, resultados, nulas, fig_g1, fig_g2, links, semente):
    repo = dict(links).get("Repositório") or ""
    corpo = "".join([
        secao_cenario(c, grafico(fig_g1, "g1-histogramas", incluir_js=True)),
        secao_nula(resultados, c["alfa"], nulas,
                   grafico(fig_g2, "g2-nula", incluir_js=False)),
        secao(3, "erro-tipo-1", "Q1: erro tipo I", pendente(
            repo, 79, "G3, proporção de rejeições com H0 verdadeira em 10.000 réplicas")),
        secao(4, "poder", "Q2: poder", pendente(
            repo, 80, "G4, curvas de poder dos dois testes")),
        secao(5, "violacoes", "Q3: violações de pressupostos", pendente(
            repo, 81, "Q1 e Q2 repetidas com σ alto, outliers e n pequeno")),
        secao(6, "dados-reais", "Os testes nos dados reais", pendente(
            repo, 82, "tabela dos dois testes nos 60 PRs coletados")),
        secao(7, "conclusao", "Conclusão", pendente(
            repo, 84, "esperado × encontrado e recomendação")),
    ])

    nav = "".join(f'<a href="#{a}">{n}. {esc(t)}</a>' for n, a, t in (
        (1, "cenario", "Cenário"), (2, "nula", "Sob H0"), (3, "erro-tipo-1", "Erro tipo I"),
        (4, "poder", "Poder"), (5, "violacoes", "Violações"), (6, "dados-reais", "Dados reais"),
        (7, "conclusao", "Conclusão")))

    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Lab 04: Welch × Mann-Whitney</title>
<style>{CSS}</style>
</head>
<body>
<header>
  <h1>Lab 04: t de Welch × Mann-Whitney</h1>
  <p class="sub">Tempo até o merge de PRs com e sem review do CodeRabbit
  (MCPJam/inspector). Gerado por <code>python -m dashboard</code>, semente {semente}.</p>
  <p class="links">{_links(links)}</p>
  <p class="cores">Cores fixas em todos os gráficos: {_legenda_cores()}</p>
  <nav>{nav}</nav>
</header>
<main>
{corpo}
</main>
</body>
</html>
"""


CSS = """
:root { --texto:#1f2328; --suave:#59636e; --borda:#d1d9e0; --fundo:#ffffff;
        --fundo2:#f6f8fa; --link:#0969da; }
* { box-sizing: border-box; }
body { margin:0; background:var(--fundo); color:var(--texto);
       font:15px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif; }
header, main { max-width:1100px; margin:0 auto; padding:0 16px; }
header { padding-top:28px; padding-bottom:12px; border-bottom:1px solid var(--borda); }
h1 { font-size:1.6rem; margin:0 0 4px; }
h2 { font-size:1.3rem; margin:40px 0 12px; padding-bottom:6px;
     border-bottom:1px solid var(--borda); }
h3 { font-size:1.05rem; margin:24px 0 8px; }
.num { color:var(--suave); }
.sub, .legenda-grafico { color:var(--suave); }
a { color:var(--link); }
.links { margin:8px 0; }
.sem-link { color:var(--suave); }
nav { display:flex; flex-wrap:wrap; gap:6px 14px; margin-top:10px; font-size:.92rem; }
.chip { display:inline-flex; align-items:center; gap:6px; margin-right:10px;
        white-space:nowrap; }
.chip i { display:inline-block; width:12px; height:12px; border-radius:2px; }
.pergunta { font-size:1.1rem; font-weight:600; }
.tabela { overflow-x:auto; margin:8px 0 12px; }
table { border-collapse:collapse; font-size:.9rem; }
th, td { border:1px solid var(--borda); padding:6px 9px; text-align:left;
         vertical-align:top; }
th { background:var(--fundo2); }
.lado-a-lado { display:flex; flex-wrap:wrap; gap:0 24px; align-items:flex-start; }
.previsao { background:var(--fundo2); border-left:4px solid var(--suave);
            padding:10px 14px; margin:16px 0; }
.pendente { color:var(--suave); font-style:italic; background:var(--fundo2);
            padding:10px 14px; border-radius:6px; }
main { padding-bottom:48px; }
"""
