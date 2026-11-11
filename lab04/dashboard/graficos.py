"""Gráficos do dashboard (issue #78).

Regra de cores: **cada teste tem uma cor fixa em todos os gráficos** (t de
Welch azul, Mann-Whitney laranja, da paleta Okabe-Ito, segura para daltonismo).
As cores de dados reais × simulados ficam fora dessa dupla para que nenhum
gráfico sugira um teste onde não há teste. Os gráficos das próximas sprints
(G3, G4) devem importar `CORES_TESTE` daqui em vez de escolher cores próprias.
"""
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats

from simulacao.cenario import GRUPO_CONTROLE, GRUPO_TRATAMENTO

CORES_TESTE = {"welch": "#0072B2", "mannwhitney": "#D55E00"}
NOMES_TESTE = {"welch": "t de Welch", "mannwhitney": "Mann-Whitney U"}
COR_REAL = "#4D4D4D"
COR_SIMULADO = "#009E73"
COR_MODELO = "#222222"

NOMES_GRUPO = {GRUPO_CONTROLE: "Sem review do bot (controle)",
               GRUPO_TRATAMENTO: "Com review do bot (tratamento)"}
# Versão curta para títulos de painel, que ficam lado a lado em telas estreitas.
NOMES_GRUPO_CURTO = {GRUPO_CONTROLE: "Sem bot (controle)",
                     GRUPO_TRATAMENTO: "Com bot (tratamento)"}

# Separadores pt-BR nos eixos e rótulos de hover.
LAYOUT_BASE = dict(template="plotly_white", separators=",.",
                   font=dict(family="system-ui, -apple-system, Segoe UI, sans-serif",
                             size=13),
                   margin=dict(l=60, r=20, t=70, b=60))

# Bins do G1 em log10(horas): de 0,001 h (~4 s) a 1000 h (~6 semanas).
BINS_LOG = dict(start=-3.0, end=3.0, size=0.25)
TICKS_LOG = [-2, 0, 2]
ROTULOS_LOG = ["0,01 h", "1 h", "100 h"]


def _rgba(hexa, alfa):
    r, g, b = (int(hexa[i:i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r},{g},{b},{alfa})"


def num(valor, casas=2):
    """Número com vírgula decimal, para rótulos."""
    return f"{valor:.{casas}f}".replace(".", ",")


def p_texto(p):
    return f"{p:.2e}".replace(".", ",") if p < 0.001 else num(p, 4)


# ---- G1 --------------------------------------------------------------------

def g1_histogramas(reais, simulados, cenario):
    """G1: histogramas reais × simulados, um painel por grupo.

    Abre em escala log, onde a lognormal vira normal e dá para comparar o
    formato com a curva do modelo; o botão "Horas" mostra a mesma coisa em
    escala linear, onde aparece a assimetria que motivou a lognormal.
    A curva do modelo é a densidade usada pelo gerador, convertida em
    contagem esperada por bin (n · largura · densidade).
    """
    grupos = (GRUPO_CONTROLE, GRUPO_TRATAMENTO)
    fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.08,
                        subplot_titles=[NOMES_GRUPO_CURTO[g] for g in grupos])

    maximo = max(float(np.max(v)) for d in (reais, simulados) for v in d.values())
    tam_linear = float(np.ceil(maximo / 30 / 5) * 5) or 1.0
    bins_lin = dict(start=0.0, end=tam_linear * 31, size=tam_linear)

    # Cada painel tem 5 traços: real/simulado em log, modelo, real/simulado em horas.
    visivel_log, visivel_lin = [], []
    mu = {GRUPO_CONTROLE: cenario["mu_controle"],
          GRUPO_TRATAMENTO: cenario["mu_controle"] + cenario["efeito_observado_log"]}
    for col, grupo in enumerate(grupos, start=1):
        mostrar_legenda = col == 1
        for origem, dados, cor in (("Real (coleta #76)", reais, COR_REAL),
                                   ("Simulado (gerador #77)", simulados, COR_SIMULADO)):
            fig.add_trace(go.Histogram(
                x=np.log10(dados[grupo]), xbins=BINS_LOG, name=origem,
                legendgroup=origem, showlegend=mostrar_legenda,
                marker=dict(color=_rgba(cor, 0.55), line=dict(color=cor, width=1)),
                hovertemplate=f"{origem}<br>%{{y}} PRs<extra></extra>"),
                row=1, col=col)

        # Densidade de log10(X): normal com média mu/ln10 e desvio sigma/ln10.
        n = simulados[grupo].size
        x = np.linspace(BINS_LOG["start"], BINS_LOG["end"], 300)
        dens = stats.norm(mu[grupo] / np.log(10),
                          cenario["sigma_comum"] / np.log(10)).pdf(x)
        fig.add_trace(go.Scatter(
            x=x, y=dens * n * BINS_LOG["size"], mode="lines",
            name="Lognormal do gerador", legendgroup="modelo",
            showlegend=mostrar_legenda, line=dict(color=COR_MODELO, dash="dash", width=2),
            hoverinfo="skip"), row=1, col=col)

        for origem, dados, cor in (("Real (coleta #76)", reais, COR_REAL),
                                   ("Simulado (gerador #77)", simulados, COR_SIMULADO)):
            fig.add_trace(go.Histogram(
                x=dados[grupo], xbins=bins_lin, name=origem, legendgroup=origem,
                showlegend=False, visible=False,
                marker=dict(color=_rgba(cor, 0.55), line=dict(color=cor, width=1)),
                hovertemplate=(f"{origem}<br>%{{x}} h<br>%{{y}} PRs<extra></extra>")),
                row=1, col=col)
        visivel_log += [True, True, True, False, False]
        visivel_lin += [False, False, False, True, True]

    eixos_log, eixos_lin = {}, {}
    for eixo in ("xaxis", "xaxis2"):
        eixos_log.update({f"{eixo}.tickvals": TICKS_LOG, f"{eixo}.ticktext": ROTULOS_LOG,
                          f"{eixo}.title.text": "horas (escala log)",
                          f"{eixo}.range": [BINS_LOG["start"], BINS_LOG["end"]]})
        eixos_lin.update({f"{eixo}.tickvals": None, f"{eixo}.ticktext": None,
                          f"{eixo}.title.text": "horas",
                          f"{eixo}.range": [0, bins_lin["end"]]})

    fig.update_layout(
        **{**LAYOUT_BASE, "margin": dict(l=60, r=20, t=100, b=60)},
        barmode="overlay", height=470,
        legend=dict(orientation="h", y=-0.25, x=0.5, xanchor="center"),
        # Botões à esquerda: à direita eles cobririam a barra de ferramentas do Plotly.
        updatemenus=[dict(
            type="buttons", direction="right", x=0.0, xanchor="left", y=1.32,
            yanchor="top", showactive=True, active=0,
            buttons=[dict(label="Escala log", method="update",
                          args=[{"visible": visivel_log}, eixos_log]),
                     dict(label="Horas", method="update",
                          args=[{"visible": visivel_lin}, eixos_lin])])])
    for col in (1, 2):
        fig.update_xaxes(tickvals=TICKS_LOG, ticktext=ROTULOS_LOG,
                         range=[BINS_LOG["start"], BINS_LOG["end"]],
                         title_text="horas (escala log)", row=1, col=col)
    fig.update_yaxes(title_text="PRs", row=1, col=1)
    return fig


# ---- G2 --------------------------------------------------------------------

def _area(fig, nula, distancia, col, nome, mostrar, **estilo):
    """Sombreia as duas caudas a `distancia` ou mais do centro da curva.

    Cada cauda é um traço separado: preencher um traço só, com buraco no meio,
    faria o Plotly ligar as duas pontas e pintar o centro.
    """
    for lado, mascara in (("esq", nula.x <= nula.centro - distancia),
                          ("dir", nula.x >= nula.centro + distancia)):
        if mascara.sum() < 2:
            continue
        fig.add_trace(go.Scatter(
            x=nula.x[mascara], y=nula.densidade[mascara], mode="lines",
            fill="tozeroy", line=dict(width=0), name=nome, legendgroup=nome,
            showlegend=mostrar and lado == "esq", hoverinfo="skip", **estilo),
            row=1, col=col)
        mostrar = mostrar and lado != "esq"


def g2_nula(nulas, resultados, alfa):
    """G2: distribuição de cada estatística sob H0, no conjunto simulado.

    Para cada teste: a curva sob H0, a região de rejeição a `alfa` (sólida), o
    p-valor do exemplo como área hachurada nas duas caudas (bicaudal) e a linha
    da estatística observada. A área hachurada é calculada com a mesma
    aproximação do scipy, então mede exatamente o p-valor da tabela.
    """
    chaves = ("welch", "mannwhitney")
    fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.08, subplot_titles=[
        f"{NOMES_TESTE[k]}: p = {p_texto(resultados[k].p_valor)}" for k in chaves])

    for col, chave in enumerate(chaves, start=1):
        nula, cor = nulas[chave], CORES_TESTE[chave]
        primeira = col == 1
        fig.add_trace(go.Scatter(
            x=nula.x, y=nula.densidade, mode="lines", name="Distribuição sob H0",
            legendgroup="h0", showlegend=primeira, line=dict(color=cor, width=2.5),
            hovertemplate="%{x:.2f}<extra>sob H0</extra>"), row=1, col=col)
        _area(fig, nula, nula.dist_critica, col, f"Região de rejeição (α = {num(alfa)})",
              primeira, fillcolor=_rgba(cor, 0.45))
        for x in (nula.centro - nula.dist_critica, nula.centro + nula.dist_critica):
            fig.add_vline(x=x, line=dict(color=cor, width=1, dash="dash"), row=1, col=col)
        _area(fig, nula, nula.dist_p, col, "p-valor (área hachurada)", primeira,
              fillcolor="rgba(0,0,0,0)",
              fillpattern=dict(shape="/", fgcolor=cor, size=7, solidity=0.35))

        topo = float(nula.densidade.max()) * 1.08
        # Linha cheia no observado e pontilhada no espelho: no bicaudal, valores
        # tão extremos quanto o observado do outro lado também contam no p.
        espelho = 2 * nula.centro - nula.observado
        for x, traco in ((nula.observado, "solid"), (espelho, "dot")):
            fig.add_trace(go.Scatter(
                x=[x, x], y=[0, topo], mode="lines",
                name="Estatística observada", legendgroup="obs",
                showlegend=primeira and traco == "solid",
                line=dict(color=COR_MODELO, width=2, dash=traco), hoverinfo="skip"),
                row=1, col=col)
        fig.add_annotation(
            x=nula.observado, y=topo,
            text=f"observado = {num(nula.observado, 2 if chave == 'welch' else 0)}",
            showarrow=False, yanchor="bottom",
            xanchor="right" if nula.observado > nula.centro else "left",
            row=1, col=col)
        fig.update_xaxes(title_text="t" if chave == "welch" else "U", row=1, col=col)

    fig.update_yaxes(title_text="densidade", row=1, col=1)
    fig.update_layout(**LAYOUT_BASE, height=430,
                      legend=dict(orientation="h", y=-0.22, x=0.5, xanchor="center"))
    return fig


# ---- G3 --------------------------------------------------------------------

# Bins do histograma de p-valores: 20 faixas de 0,05 fazem a faixa p < 0,05,
# que é a que decide a rejeição, coincidir exatamente com a primeira barra.
BINS_P = 20


def g3_erro_tipo1(resultados, alfa):
    """G3: erro tipo I dos dois testes em réplicas com H0 verdadeira.

    Painel da esquerda: distribuição dos p-valores sob H0. Um teste calibrado
    produz p-valores uniformes, isto é, barras na linha tracejada; barras baixas
    na ponta esquerda significam que o teste quase nunca chega a p pequeno.

    Painel da direita: taxa de rejeição observada contra o α nominal. A
    diagonal é a calibração perfeita; abaixo dela o teste é conservador e acima
    é anticonservador. O ponto destacado é o α do estudo, com o intervalo de
    confiança de 95% da estimativa.
    """
    chaves = ("welch", "mannwhitney")
    qualquer = resultados[chaves[0]]
    fig = make_subplots(
        rows=1, cols=2, horizontal_spacing=0.11,
        subplot_titles=(f"p-valores sob H0 ({qualquer.taxa.repeticoes:,} réplicas)"
                        .replace(",", "."),
                        "Taxa de rejeição × α nominal"))

    esperado = qualquer.taxa.repeticoes / BINS_P
    for chave in chaves:
        r, cor = resultados[chave], CORES_TESTE[chave]
        fig.add_trace(go.Histogram(
            x=r.p_valores, xbins=dict(start=0.0, end=1.0, size=1.0 / BINS_P),
            name=NOMES_TESTE[chave], legendgroup=chave,
            marker=dict(color=_rgba(cor, 0.55), line=dict(color=cor, width=1)),
            hovertemplate=f"{NOMES_TESTE[chave]}<br>p em %{{x}}<br>"
                          "%{y} réplicas<extra></extra>"), row=1, col=1)

    fig.add_hline(y=esperado, line=dict(color=COR_MODELO, width=2, dash="dash"),
                  annotation_text="uniforme (teste calibrado)",
                  annotation_position="top right", row=1, col=1)
    # Marca a faixa que decide a rejeição: tudo à esquerda dela é um falso
    # positivo, já que aqui H0 é verdadeira por construção.
    fig.add_vrect(x0=0.0, x1=alfa, fillcolor=_rgba(COR_MODELO, 0.12), line_width=0,
                  annotation_text=f"p &lt; {num(alfa)}: falso positivo",
                  annotation_position="top right", annotation_xshift=4,
                  annotation=dict(xanchor="left", font=dict(size=11)),
                  row=1, col=1)

    limite = float(qualquer.alfas.max())
    fig.add_trace(go.Scatter(
        x=[0, limite], y=[0, limite], mode="lines", name="Calibração perfeita",
        legendgroup="diagonal", line=dict(color=COR_MODELO, width=2, dash="dash"),
        hoverinfo="skip"), row=1, col=2)

    for chave in chaves:
        r, cor = resultados[chave], CORES_TESTE[chave]
        fig.add_trace(go.Scatter(
            x=r.alfas, y=r.calibracao, mode="lines+markers", name=NOMES_TESTE[chave],
            legendgroup=chave, showlegend=False, line=dict(color=cor, width=2.5),
            marker=dict(size=6),
            hovertemplate=f"{NOMES_TESTE[chave]}<br>α = %{{x}}<br>"
                          "rejeita em %{y:.2%}<extra></extra>"), row=1, col=2)
        fig.add_trace(go.Scatter(
            x=[r.alfa], y=[r.taxa.taxa], mode="markers", name=NOMES_TESTE[chave],
            legendgroup=chave, showlegend=False,
            marker=dict(size=13, color=cor, symbol="circle",
                        line=dict(color="white", width=2)),
            error_y=dict(type="data", symmetric=False,
                         array=[r.taxa.ic_alto - r.taxa.taxa],
                         arrayminus=[r.taxa.taxa - r.taxa.ic_baixo],
                         color=cor, thickness=1.5, width=6),
            hovertemplate=(f"{NOMES_TESTE[chave]} em α = {num(r.alfa)}<br>"
                           f"erro tipo I = {num(r.taxa.taxa * 100)}%<br>"
                           f"IC 95%: {num(r.taxa.ic_baixo * 100)}% a "
                           f"{num(r.taxa.ic_alto * 100)}%<extra></extra>")),
            row=1, col=2)

    fig.update_xaxes(title_text="p-valor", range=[0, 1], row=1, col=1)
    fig.update_yaxes(title_text="réplicas", row=1, col=1)
    fig.update_xaxes(title_text="α nominal", range=[0, limite * 1.03], row=1, col=2)
    fig.update_yaxes(title_text="taxa de rejeição observada",
                     range=[0, limite * 1.03], row=1, col=2)
    fig.update_layout(**{**LAYOUT_BASE, "margin": dict(l=60, r=20, t=70, b=70)},
                      barmode="overlay", height=450,
                      legend=dict(orientation="h", y=-0.24, x=0.5, xanchor="center"))
    return fig


# ---- Q3 (#81) --------------------------------------------------------------

def g_violacoes(res, alfa):
    """Q3: erro tipo I (barras) e poder (curvas) nos cenários de `sim.CENARIOS`.

    `res` é o DataFrame de `sim.simular_tudo()`; as chaves de teste de lá
    (`mann_whitney`) são mapeadas para as daqui (`mannwhitney`).
    """
    import sim
    chave = {"welch": "welch", "mann_whitney": "mannwhitney"}
    rotulos = {c: v["rotulo"] for c, v in sim.CENARIOS.items()}
    fig = make_subplots(rows=1, cols=2, column_widths=[0.42, 0.58], horizontal_spacing=0.1,
                        subplot_titles=("Erro tipo I sob H0 (deveria ser 5%)",
                                        "Poder com a mediana dobrada (razão 2×)"))
    for teste_sim, teste in chave.items():
        for col, ef in ((1, 1.0), (2, 2.0)):
            s = res[(res.teste == teste_sim) & (res.efeito == ef)]
            fig.add_bar(x=[rotulos[c] for c in s.cenario], y=s.taxa, name=NOMES_TESTE[teste],
                        marker_color=CORES_TESTE[teste], legendgroup=teste, showlegend=col == 1,
                        error_y=dict(type="data", array=s.ic_sup - s.taxa,
                                     arrayminus=s.taxa - s.ic_inf),
                        text=[f"{v:.1%}".replace(".", ",") for v in s.taxa],
                        textposition="outside", row=1, col=col)
    fig.add_hline(y=alfa, line_dash="dash", line_color="#cf222e", row=1, col=1,
                  annotation_text="α = 5%")
    fig.update_yaxes(tickformat=".0%")
    fig.update_layout(barmode="group", template="plotly_white", height=480,
                      margin=dict(t=60, l=50, r=20, b=40),
                      legend=dict(orientation="h", y=1.14, x=0))
    return fig
