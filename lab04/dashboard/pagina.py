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
from simulacao.cenario import PREVISOES


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


# As descrições curtas de cada veredito ficam aqui, e não em experimentos.py,
# porque são texto de apresentação: o módulo de simulação devolve só o rótulo.
VEREDITOS = {
    "calibrado": "rejeita na taxa prometida",
    "conservador": "rejeita menos que o prometido — perde poder",
    "anticonservador": "rejeita mais que o prometido — falsos positivos a mais",
}


def secao_erro_tipo1(erros, alfa, fig_g3):
    """Seção 3: Q1, erro tipo I medido em réplicas com H0 verdadeira."""
    qualquer = next(iter(erros.values()))
    repeticoes = f"{qualquer.taxa.repeticoes:,}".replace(",", ".")

    linhas = []
    for chave, r in erros.items():
        linhas.append((
            f'<span class="chip"><i style="background:{CORES_TESTE[chave]}"></i>'
            f"{esc(NOMES_TESTE[chave])}</span>",
            f"{r.taxa.rejeicoes} / {repeticoes}",
            f"<strong>{num(r.taxa.taxa * 100)}%</strong>",
            f"{num(r.taxa.ic_baixo * 100)}% a {num(r.taxa.ic_alto * 100)}%",
            f"{num(r.razao)}×",
            p_texto(r.p_minimo),
            f'<strong>{esc(r.veredito)}</strong>: {esc(VEREDITOS[r.veredito])}',
        ))
    tab = tabela(["Teste", "Falsos positivos", "Erro tipo I observado",
                  "IC 95% da estimativa", "Observado ÷ nominal",
                  f"Menor p em {repeticoes} réplicas", "Veredito"], linhas)

    welch, mw = erros["welch"], erros["mannwhitney"]
    return secao(3, "erro-tipo-1", "Q1: erro tipo I", f"""
<p>Geramos <strong>{repeticoes} réplicas</strong> do experimento com os dois grupos
saindo da <em>mesma</em> lognormal, isto é, com efeito zero: aqui H0 é verdadeira
por construção e <strong>toda rejeição é um falso positivo</strong>. A proporção de
rejeições estima o erro tipo I real de cada teste, que deveria bater com o α nominal
de {num(alfa * 100, 0)}%. Os dois testes veem exatamente as mesmas amostras, então a
diferença entre eles não pode ser atribuída à sorte do sorteio.</p>
{tab}
<h3>G3: p-valores sob H0 e calibração</h3>
<p class="legenda-grafico">À esquerda, a distribuição dos p-valores quando H0 é
verdadeira: um teste calibrado produz p-valores uniformes, ou seja, barras na altura
da linha tracejada em toda a faixa. À direita, a taxa de rejeição observada contra o
α nominal — a diagonal é a calibração perfeita, abaixo dela o teste é conservador e
acima é anticonservador. O ponto destacado é α = {num(alfa)}, com intervalo de
confiança de 95%.</p>
{fig_g3}
<div class="achado">
<p><strong>O t de Welch é fortemente conservador neste cenário.</strong> Ele rejeita
em {num(welch.taxa.taxa * 100)}% das réplicas quando deveria rejeitar em
{num(alfa * 100, 0)}% — cerca de {num(1 / welch.razao, 1)} vezes menos. O histograma
mostra por quê: em vez de uniformes, os p-valores do Welch se amontoam entre 0,2 e
0,4 e quase nunca chegam perto de zero. Em {repeticoes} tentativas o menor p-valor
que ele produziu foi {p_texto(welch.p_minimo)}; com dados desta assimetria, um
resultado a 1% de significância é simplesmente inalcançável para ele.</p>
<p><strong>O Mann-Whitney fica calibrado.</strong> Rejeita em
{num(mw.taxa.taxa * 100)}% das réplicas, com o α nominal dentro do intervalo de
confiança, e sua curva acompanha a diagonal em toda a faixa de α. Ele não supõe
normalidade, então a assimetria da lognormal não o afeta.</p>
<p>Um teste conservador não produz falsos positivos a mais — nesse sentido o Welch
é "seguro". O preço aparece na Q2: quem rejeita de menos sob H0 também rejeita de
menos quando existe efeito de verdade, e é por isso que o Welch não acusou a
diferença do exemplo da seção 2 enquanto o Mann-Whitney acusou.</p>
</div>
""")


# Cor de fundo de cada veredito da conclusão. Verde/amarelo/vermelho seriam
# ilegíveis para parte dos daltônicos, então a distinção é feita pelo próprio
# rótulo escrito e o fundo é só um reforço.
CLASSES_VEREDITO = {"confirmada": "ok", "parcial": "meio", "refutada": "nao",
                    "pendente": "aberto"}


def secao_conclusao(c, avaliacoes, contagem, repo):
    """Seção 7: previsto × encontrado, recomendação e limites (issue #84)."""
    linhas = []
    for a, previsao in zip(avaliacoes, PREVISOES):
        encontrado = (markdown_simples(a.encontrado) if a.resolvida else
                      f'<em>ainda não rodado — issue '
                      f'<a href="{esc(repo)}/issues/{a.issue}">#{a.issue}</a></em>')
        linhas.append((
            markdown_simples(a.previsto),
            esc(previsao["decide"]),
            encontrado,
            f'<span class="veredito {CLASSES_VEREDITO[a.veredito]}">'
            f"{esc(a.veredito)}</span>",
        ))
    tab = tabela(["Previsto (registrado antes de simular)", "Decidido por",
                  "Encontrado", "Veredito"], linhas)

    resolvidas = sum(n for v, n in contagem.items() if v != "pendente")
    abertura = (f"Das {len(avaliacoes)} previsões registradas antes de qualquer "
                f"simulação repetida, {resolvidas} já têm resposta: "
                + ", ".join(f"{n} {v}{'s' if n > 1 else ''}"
                            for v, n in contagem.items() if n and v != "pendente")
                + ".")
    if contagem["pendente"]:
        abertura += (f" A{'s' if contagem['pendente'] > 1 else ''} outra"
                     f"{'s' if contagem['pendente'] > 1 else ''} depende"
                     f"{'m' if contagem['pendente'] > 1 else ''} de experimentos "
                     "ainda não rodados, marcados na tabela.")

    return secao(7, "conclusao", "Conclusão", f"""
<p>{esc(abertura)}</p>
<h3>Previsto × encontrado</h3>
{tab}
<h3>Recomendação</h3>
<div class="achado"><p>{markdown_simples(c["recomendacao"])}</p></div>
<h3>O que este estudo não mostra</h3>
<ul>
<li><strong>O resultado é deste cenário, não universal.</strong> Tudo foi medido
numa lognormal com σ(log) ≈ {num(c["sigma_comum"], 1)} e n = {c["n_por_grupo"]}
por grupo. Com dados menos assimétricos ou amostras maiores o t de Welch se
recupera — o próprio código mostra isso quando σ é reduzido.</li>
<li><strong>Nada aqui é causal.</strong> O bot não foi sorteado entre os PRs;
os dados reais serviram só para calibrar parâmetros realistas da simulação.</li>
<li><strong>Um p-valor não mede importância.</strong> Por isso todo teste
aparece acompanhado do seu tamanho de efeito, e a recomendação pede que os dois
sejam relatados juntos.</li>
</ul>
""")


def secao_violacoes(res, fig):
    """Seção 5 (#81): Q1 e Q2 repetidas em cenários que violam o t."""
    import sim
    linhas = []
    for c, v in sim.CENARIOS.items():
        def t(ef, teste):
            r = res[(res.cenario == c) & (res.efeito == ef) & (res.teste == teste)].iloc[0]
            return f"{r.taxa:.1%}".replace(".", ",")
        linhas.append([esc(v["rotulo"]), t(1.0, "welch"), t(1.0, "mann_whitney"),
                       t(2.0, "welch"), t(2.0, "mann_whitney")])
    return secao(5, "violacoes", "Q3: violações de pressupostos", f"""
<p>Repetimos Q1 (H0 verdadeira) e Q2 (mediana do grupo com bot 2× maior) em três
situações que violam o que o teste t assume, com 10.000 réplicas por ponto e
semente fixa: <strong>assimetria mais forte</strong> (σ do log ×1,5),
<strong>contaminação por outliers</strong> (10% das observações multiplicadas
por 20) e <strong>amostra pequena</strong> (n = 10 por grupo). Os bigodes são o
IC 95% de Wilson.</p>
{grafico(fig, "g-violacoes", incluir_js=False)}
{tabela(["Cenário", "Tipo I Welch", "Tipo I Mann-Whitney", "Poder Welch (2×)",
         "Poder Mann-Whitney (2×)"], linhas)}
<div class="achado"><p>Quanto mais forte a violação, mais o t de Welch fica
<strong>conservador</strong> e perde poder: com assimetria forte ele rejeita
menos de 1% sob H0 e quase nunca detecta a mediana dobrada. Em dados lognormais a
variância amostral é inflada pelos valores extremos e o t raramente fica grande.
O Mann-Whitney mantém o erro tipo I perto de 5% em todos os cenários, porque usa
só a ordem dos dados: assimetria e tamanho dos outliers não mudam os postos.</p></div>
<p class="legenda-grafico">Exploração interativa destes cenários (sliders de efeito,
n, σ e outliers): <a href="../painel/">painel interativo</a>.</p>
""")


def secao_dados_reais(reais):
    """Seção 6 (#82): os dois testes nos 60 PRs coletados."""
    linhas = [[esc(r["teste"]), esc(r["estatistica"].replace(".", ",")),
               p_texto(r["p"]), esc(r["efeito"].replace(".", ",")),
               f'<span class="veredito {"ok" if r["p"] < 0.05 else "aberto"}">'
               f'{esc(r["conclusao"])}</span>'] for r in reais]
    pw, pm = reais[0]["p"], reais[1]["p"]
    return secao(6, "dados-reais", "Os testes nos dados reais", f"""
<p>Os dois testes aplicados aos 60 PRs coletados (30 por grupo), bicaudais, α = 5%.</p>
{tabela(["Teste", "Estatística", "p-valor", "Tamanho de efeito", "Conclusão"], linhas)}
<div class="achado"><p>Os dois testes rejeitam H0: PRs revisados pelo CodeRabbit
levam mais tempo até o merge, com mediana cerca de 5× maior. A evidência do
Mann-Whitney (p = {p_texto(pm)}) é ~{round(pw / pm)}× mais forte que a do Welch
(p = {p_texto(pw)}), que passa raspando, como previa a simulação: com esta
assimetria o Welch tem pouco poder. Cliff δ = 0,47 está no limite de um efeito
grande (|δ| ≥ 0,474, Romano et al.); o Cohen d é pouco confiável aqui porque
média e desvio são puxados por poucos PRs muito longos (máx. 203 h).</p></div>
<p><strong>Limitação:</strong> estudo observacional. O bot não foi sorteado entre os
PRs, e os que ele revisa podem ser maiores ou de outros autores; a diferença é
uma associação, não um efeito causal do bot.</p>
""")


def montar(c, resultados, nulas, fig_g1, fig_g2, links, semente,
           erros_tipo1=None, fig_g3=None, avaliacoes=None, contagem=None,
           violacoes=None, fig_violacoes=None, reais=None):
    repo = dict(links).get("Repositório") or ""
    corpo = "".join([
        secao_cenario(c, grafico(fig_g1, "g1-histogramas", incluir_js=True)),
        secao_nula(resultados, c["alfa"], nulas,
                   grafico(fig_g2, "g2-nula", incluir_js=False)),
        secao_erro_tipo1(erros_tipo1, c["alfa"],
                         grafico(fig_g3, "g3-erro-tipo-1", incluir_js=False))
        if erros_tipo1 else
        secao(3, "erro-tipo-1", "Q1: erro tipo I", pendente(
            repo, 79, "G3, proporção de rejeições com H0 verdadeira em 10.000 réplicas")),
        secao(4, "poder", "Q2: poder", pendente(
            repo, 80, "G4, curvas de poder dos dois testes")),
        secao_violacoes(violacoes, fig_violacoes) if violacoes is not None else
        secao(5, "violacoes", "Q3: violações de pressupostos", pendente(
            repo, 81, "Q1 e Q2 repetidas com σ alto, outliers e n pequeno")),
        secao_dados_reais(reais) if reais else
        secao(6, "dados-reais", "Os testes nos dados reais", pendente(
            repo, 82, "tabela dos dois testes nos 60 PRs coletados")),
        secao_conclusao(c, avaliacoes, contagem, repo) if avaliacoes else
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
.veredito { display:inline-block; padding:1px 8px; border-radius:10px;
            font-size:.85rem; font-weight:600; white-space:nowrap;
            border:1px solid var(--borda); }
.veredito.ok { background:#dafbe1; }
.veredito.meio { background:#fff1cc; }
.veredito.nao { background:#ffe3e3; }
.veredito.aberto { background:var(--fundo2); color:var(--suave);
                   font-weight:400; font-style:italic; }
section ul { margin:8px 0 12px; padding-left:22px; }
section li { margin:6px 0; }
.achado { background:var(--fundo2); border-left:4px solid var(--link);
          padding:2px 14px; margin:16px 0; }
.achado p { margin:12px 0; }
.pendente { color:var(--suave); font-style:italic; background:var(--fundo2);
            padding:10px 14px; border-radius:6px; }
main { padding-bottom:48px; }
"""
