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
