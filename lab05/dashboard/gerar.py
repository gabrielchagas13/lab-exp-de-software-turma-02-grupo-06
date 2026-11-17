"""Gera o dashboard do Lab05 (dashboard/index.html).

Lê os CSVs já coletados (Lighthouse, disponibilidade, SEJUSP) e monta uma
página única com Plotly. As seções sem dados ainda aparecem como
"em construção", apontando para quem é responsável.

    python -m dashboard.gerar
"""
import html
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

from analise import sejusp

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "dashboard" / "index.html"

COR_MOBILE = "#c2410c"
COR_DESKTOP = "#1d4ed8"
COR_NEUTRA = "#475569"
COR_DESTAQUE = "#b91c1c"

NOMES_PAGINA = {
    "dv_inicio": "Delegacia Virtual (início)",
    "mg_servico_reds": "mg.gov.br: serviço REDS",
    "mg_servico_perda_doc": "mg.gov.br: perda de documento",
}

# Uso da Delegacia Virtual (fonte: Tribuna de Minas, 30/04/2021): 205,8 mil
# registros de jan. a nov. de 2020, levado para 12 meses.
REGISTROS_ANO_2020 = round(205_800 / 11 * 12)

_n_fig = 0


def esc(t):
    return html.escape(str(t))


def fig_html(fig):
    global _n_fig
    _n_fig += 1
    fig.update_layout(
        template="plotly_white", margin=dict(l=50, r=20, t=40, b=40), height=360,
        font=dict(family="Inter, system-ui, sans-serif", size=13, color="#64748b"),
        xaxis=dict(gridcolor="rgba(128,128,128,.2)"), yaxis=dict(gridcolor="rgba(128,128,128,.2)"),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=-0.15, x=0),
    )
    return fig.to_html(full_html=False, include_plotlyjs=False, div_id=f"g{_n_fig}",
                       config={"displaylogo": False, "responsive": True})


def kpi(valor, rotulo, nota=""):
    n = f'<div class="kpi-nota">{esc(nota)}</div>' if nota else ""
    return f'<div class="kpi"><div class="kpi-valor">{esc(valor)}</div><div class="kpi-rot">{esc(rotulo)}</div>{n}</div>'


def secao(num, ancora, titulo, corpo):
    return f'<section id="{ancora}"><h2><span class="num">{num}</span>{esc(titulo)}</h2>{corpo}</section>'


def pendente(texto, quem):
    return f'<p class="pendente">Em construção: {esc(texto)} <strong>({esc(quem)})</strong></p>'


def tabela(cab, linhas):
    th = "".join(f"<th>{esc(c)}</th>" for c in cab)
    trs = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in l) + "</tr>" for l in linhas)
    return f'<div class="tabela"><table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>'


# ---------- seções ----------

def sec_software():
    corpo = '<div class="kpis">' + "".join([
        kpi("2014", "no ar desde", "30/04/2014"),
        kpi("1,5 mi+", "boletins online até abr/2021", "Tribuna de Minas"),
        kpi("~68%", "dos registros são perda de documento", "Agência Minas"),
        kpi(f"{REGISTROS_ANO_2020/1000:,.0f} mil".replace(",", "."), "registros online/ano (2020)", "estimado de jan–nov"),
    ]) + "</div>"
    corpo += tabela(["Critério", "Evidência"], [
        ["Real", "Sistema oficial da PCMG em delegaciavirtual.sids.mg.gov.br, listado no portal mg.gov.br"],
        ["Em operação", "Respondeu HTTP 200 no piloto de 17/11/2026; o registro online vale como o presencial"],
        ["Alto impacto", "Mais de 1,5 milhão de boletins em 7 anos; o pedido LAI vai atualizar o número"],
    ])
    return secao("01", "software", "O software: Delegacia Virtual da PCMG", corpo)


def sec_perguntas():
    linhas = [
        ["RQ1", "A Delegacia Virtual é acessível?", "Qualidade do produto", "Piloto feito"],
        ["RQ2", "O sistema é rápido no celular?", "Qualidade do produto", "Piloto feito"],
        ["RQ3", "O sistema é seguro?", "Qualidade do produto", "A coletar"],
        ["RQ4", "Qual demanda ele atende e como ela mudou?", "Dados de operação", "Série SEJUSP pronta"],
        ["RQ5", "Quanto isso custa ao cidadão?", "Impacto", "Estimativa preliminar"],
    ]
    return secao("02", "perguntas", "Perguntas de pesquisa",
                 tabela(["", "Pergunta", "Caminho", "Situação"], linhas))


def sec_qualidade():
    lh = pd.read_csv(RAIZ / "data/lighthouse/resultados.csv")
    lh = lh[lh.erro.isna()]
    agg = lh.groupby(["pagina", "dispositivo"]).agg(
        lcp=("lcp_ms", "median"), acess=("nota_acessibilidade", "median"),
        perf=("nota_performance", "median"), peso=("peso_total_kb", "median"),
        n=("lcp_ms", "size")).reset_index()
    paginas = [p for p in NOMES_PAGINA if p in set(agg.pagina)]
    nomes = [NOMES_PAGINA[p] for p in paginas]

    f1 = go.Figure()
    for disp, cor, rot in (("mobile", COR_MOBILE, "Celular"), ("desktop", COR_DESKTOP, "Computador")):
        d = agg[agg.dispositivo == disp].set_index("pagina").reindex(paginas)
        f1.add_bar(x=nomes, y=d.lcp / 1000, name=rot, marker_color=cor,
                   text=[f"{v/1000:.1f} s" for v in d.lcp], textposition="outside")
    f1.add_hline(y=2.5, line_dash="dash", line_color=COR_NEUTRA,
                 annotation_text="limite \"bom\" do Core Web Vitals (2,5 s)", annotation_position="top right")
    f1.update_layout(title="RQ2: tempo até o conteúdo principal aparecer (LCP)", yaxis_title="segundos", barmode="group")

    f2 = go.Figure()
    d = agg[agg.dispositivo == "mobile"].set_index("pagina").reindex(paginas)
    f2.add_bar(x=nomes, y=d.acess, marker_color=[COR_DESTAQUE if p == "dv_inicio" else COR_NEUTRA for p in paginas],
               text=d.acess.astype(int), textposition="outside")
    f2.update_layout(title="RQ1: nota de acessibilidade (Lighthouse, 0–100)", yaxis_range=[0, 105], showlegend=False)

    viol = lh[lh.pagina == "dv_inicio"].violacoes_acessibilidade.dropna()
    ids = sorted({v for linha in viol for v in linha.split("|")})
    explic = {
        "color-contrast": "texto com pouco contraste: difícil de ler com baixa visão",
        "html-has-lang": "página sem idioma declarado: o leitor de tela pode ler com pronúncia errada",
        "image-alt": "imagens sem descrição: invisíveis para quem usa leitor de tela",
        "link-name": "links sem nome: o leitor de tela anuncia só \"link\"",
        "tabindex": "ordem de tabulação forçada: navegar pelo teclado fica confuso",
    }
    lista = "".join(f"<li><code>{esc(i)}</code>: {esc(explic.get(i, ''))}</li>" for i in ids)

    n_med = int(agg.n.max()) if len(agg) else 0
    corpo = (f'<p class="aviso">Piloto de 17/11/2026: {n_med} medição por página e dispositivo. '
             "Os números vão mudar com as repetições da semana 1.</p>"
             f'<div class="grade2"><div>{fig_html(f1)}</div><div>{fig_html(f2)}</div></div>'
             f"<h3>Barreiras encontradas na Delegacia Virtual</h3><ul>{lista}</ul>"
             "<p><strong>Primeira leitura:</strong> a Delegacia Virtual carrega rápido, mas é a menos acessível. "
             "As páginas do mg.gov.br que levam o cidadão até ela são acessíveis, mas lentas no celular (~7 s).</p>")
    corpo += pendente("telas internas do fluxo \"perda de documento\", 3G, 5 rodadas por tela e Wilcoxon celular × computador", "Marcus / Guilherme")
    corpo += pendente("teste manual com teclado e VoiceOver (RQ1)", "Gabriel")
    return secao("03", "qualidade", "Qualidade do produto (RQ1 e RQ2)", corpo)


def sec_seguranca():
    return secao("04", "seguranca", "Segurança (RQ3)",
                 pendente("cabeçalhos HTTP, TLS e bibliotecas JS com CVEs conhecidas (coleta/seguranca.py)", "Marcus"))


def sec_demanda():
    furtos = sejusp.carregar_furtos()
    serie = sejusp.serie_mensal(furtos)
    pand = sejusp.efeito_pandemia(serie)
    saz = sejusp.sazonalidade(serie)

    f1 = go.Figure()
    f1.add_vrect(x0="2020-03-01", x1="2021-12-31", fillcolor=COR_MOBILE, opacity=0.1, line_width=0,
                 annotation_text="pandemia", annotation_position="top left")
    f1.add_vline(x="2014-04-30", line_dash="dot", line_color=COR_NEUTRA)
    f1.add_annotation(x="2014-04-30", y=1, yref="paper", text="Delegacia Virtual no ar", showarrow=False,
                      xanchor="left", yanchor="top", font=dict(color=COR_NEUTRA))
    f1.add_scatter(x=serie.data, y=serie.registros, mode="lines", line=dict(color=COR_DESKTOP, width=2),
                   name="furtos/mês", hovertemplate="%{x|%b/%Y}: %{y:,.0f}<extra></extra>")
    f1.update_layout(title="Furtos consumados registrados por mês em MG (2012–2026)", yaxis_title="registros", showlegend=False)

    meses = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
    f2 = go.Figure()
    f2.add_bar(x=meses, y=saz.values, marker_color=[COR_MOBILE if v > 0 else COR_DESKTOP for v in saz.values],
               text=[f"{v:+.1f}%" for v in saz.values], textposition="outside")
    f2.update_layout(title="Sazonalidade: desvio de cada mês em relação à média do ano", yaxis_title="%",
                     yaxis_range=[-10, 10], showlegend=False)

    reg = sejusp.por_rmbh(furtos)
    reg = reg.loc[sejusp.anos_completos(serie)]
    f3 = go.Figure()
    for col, cor, rot in (("SIM", COR_DESKTOP, "Região metropolitana de BH"), ("NÃO", COR_MOBILE, "Interior")):
        if col in reg:
            f3.add_scatter(x=reg.index, y=reg[col], mode="lines+markers", name=rot, line=dict(color=cor))
    f3.update_layout(title="Furtos por ano: região metropolitana × interior", yaxis_title="registros")

    corpo = '<div class="kpis">' + "".join([
        kpi(f"{pand['queda_vs_2019_pct']:.0f}%", "furtos no isolamento (abr–jul/2020)", "contra o mesmo período de 2019"),
        kpi(f"±{saz.abs().max():.0f}%", "maior variação sazonal", "não há pico de demanda no ano"),
        kpi(f"{serie.registros.sum()/1e6:.1f} mi".replace(".", ","), "furtos registrados 2012–2026", "SEJUSP, dados abertos"),
    ]) + "</div>"
    corpo += fig_html(f1)
    corpo += f'<div class="grade2"><div>{fig_html(f2)}</div><div>{fig_html(f3)}</div></div>'
    corpo += ('<p class="aviso"><strong>Limite:</strong> são crimes registrados por qualquer canal, não boletins da '
              "Delegacia Virtual. Mostram a demanda potencial. O uso real do sistema vem da imprensa e do pedido LAI.</p>")
    corpo += pendente("série de registros online por ano e tipo (resposta da LAI)", "Gabriel")
    return secao("05", "demanda", "Demanda atendida (RQ4)", corpo)


def sec_impacto():
    lh = pd.read_csv(RAIZ / "data/lighthouse/resultados.csv")
    lcp_mob = lh[(lh.pagina == "dv_inicio") & (lh.dispositivo == "mobile")].lcp_ms.median() / 1000
    corpo = f"""
<p>Quantas horas por ano os cidadãos passam esperando a Delegacia Virtual carregar no celular?
Ajuste as suposições: o resultado muda na hora.</p>
<div class="calc">
  <label>Registros online por ano <input id="c-reg" type="number" value="{REGISTROS_ANO_2020}" step="1000"></label>
  <label>Telas até concluir o boletim <input id="c-telas" type="number" value="5" min="1" max="20"></label>
  <label>Segundos de espera por tela (celular) <input id="c-seg" type="number" value="{lcp_mob:.1f}" step="0.1"></label>
</div>
<div class="kpis"><div class="kpi grande"><div class="kpi-valor" id="c-res">–</div>
<div class="kpi-rot">horas por ano esperando a tela carregar</div><div class="kpi-nota" id="c-dias"></div></div></div>
<p class="aviso"><strong>O que não dá para afirmar:</strong> não sabemos a fração de acessos pelo celular,
o número de telas é suposto e o tempo de preenchimento (o maior) fica de fora. O valor padrão de espera
é o LCP da página inicial no piloto; será trocado pela mediana medida em cada tela do fluxo.</p>
<script>
(function(){{
  const f = id => document.getElementById(id);
  function calc(){{
    const h = (+f('c-reg').value) * (+f('c-telas').value) * (+f('c-seg').value) / 3600;
    f('c-res').textContent = Math.round(h).toLocaleString('pt-BR') + ' h';
    f('c-dias').textContent = '≈ ' + (h/24).toLocaleString('pt-BR', {{maximumFractionDigits:1}}) + ' dias inteiros';
  }}
  ['c-reg','c-telas','c-seg'].forEach(i => f(i).addEventListener('input', calc));
  calc();
}})();
</script>"""
    corpo += pendente("cenários com o tempo medido em cada tela, 3G × 4G, e população com deficiência visual em MG (IBGE)", "Guilherme")
    return secao("06", "impacto", "Impacto para o cidadão (RQ5)", corpo)


CSS = """
:root{--bg:#f8fafc;--card:#fff;--txt:#0f172a;--sub:#475569;--borda:#e2e8f0;--acento:#1d4ed8;--aviso:#fef3c7;--pend:#f1f5f9}
@media (prefers-color-scheme:dark){:root{--bg:#0b1220;--card:#111a2e;--txt:#e2e8f0;--sub:#94a3b8;--borda:#1e293b;--acento:#60a5fa;--aviso:#3a2e0a;--pend:#1e293b}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--txt);font:15px/1.55 Inter,system-ui,sans-serif}
header{background:var(--acento);color:#fff;padding:28px 16px}header .w,main{max-width:1100px;margin:0 auto}
header h1{margin:0 0 6px;font-size:1.7rem}header p{margin:0;opacity:.9}
nav{position:sticky;top:0;background:var(--card);border-bottom:1px solid var(--borda);z-index:5;overflow-x:auto;white-space:nowrap}
nav a{display:inline-block;padding:10px 12px;color:var(--sub);text-decoration:none;font-size:.9rem}nav a:hover{color:var(--acento)}
main{padding:16px}section{background:var(--card);border:1px solid var(--borda);border-radius:12px;padding:20px;margin:18px 0}
h2{margin:0 0 14px;font-size:1.3rem}.num{color:var(--acento);margin-right:10px;font-variant-numeric:tabular-nums}h3{font-size:1.05rem}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:12px 0}
.kpi{border:1px solid var(--borda);border-radius:10px;padding:14px}.kpi-valor{font-size:1.7rem;font-weight:700;color:var(--acento)}
.kpi.grande .kpi-valor{font-size:2.4rem}.kpi-rot{font-weight:600}.kpi-nota{color:var(--sub);font-size:.85rem}
.grade2{display:grid;grid-template-columns:1fr;gap:12px}
.tabela{overflow-x:auto}table{border-collapse:collapse;width:100%}th,td{text-align:left;padding:8px;border-bottom:1px solid var(--borda)}
.aviso{background:var(--aviso);padding:10px 12px;border-radius:8px}.pendente{background:var(--pend);padding:10px 12px;border-radius:8px;color:var(--sub);border-left:4px solid var(--sub)}
.calc{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}.calc label{display:flex;flex-direction:column;font-weight:600;gap:4px}
.calc input{padding:8px;border:1px solid var(--borda);border-radius:6px;background:var(--bg);color:var(--txt);font-size:1rem}
code{background:var(--pend);padding:1px 5px;border-radius:4px}footer{color:var(--sub);text-align:center;padding:20px 16px;font-size:.85rem}
"""


def main():
    secoes = [sec_software(), sec_perguntas(), sec_qualidade(), sec_seguranca(), sec_demanda(), sec_impacto()]
    nav = "".join(f'<a href="#{a}">{t}</a>' for a, t in [
        ("software", "Software"), ("perguntas", "Perguntas"), ("qualidade", "Qualidade"),
        ("seguranca", "Segurança"), ("demanda", "Demanda"), ("impacto", "Impacto")])
    pagina = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Delegacia Virtual MG</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script><style>{CSS}</style></head><body>
<header><div class="w"><h1>A Delegacia Virtual de MG atende bem quem precisa dela?</h1>
<p>Lab05 · Grupo 06 · acessibilidade, desempenho, segurança e demanda de um serviço público em produção</p></div></header>
<nav>{nav}</nav><main>{''.join(secoes)}</main>
<footer>Gerado por <code>python -m dashboard.gerar</code> a partir de <code>lab05/data/</code>.</footer></body></html>"""
    SAIDA.write_text(pagina, encoding="utf-8")
    print(f"Dashboard salvo em {SAIDA}")


if __name__ == "__main__":
    main()
