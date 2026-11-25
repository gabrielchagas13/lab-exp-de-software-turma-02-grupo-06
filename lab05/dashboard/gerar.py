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

from analise import checklist_wcag, desempenho, impacto, sejusp
from analise import seguranca as an_seg

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "dashboard" / "index.html"

COR_MOBILE = "#c2410c"
COR_DESKTOP = "#1d4ed8"
COR_NEUTRA = "#475569"
COR_DESTAQUE = "#b91c1c"

NOMES_PAGINA = {
    "mg_servico_perda_doc": "mg.gov.br: perda de documento",
    "dv_inicio": "Delegacia Virtual (início)",
    "dv_perda_alerta": "DV: alerta (perda de doc.)",
    "dv_perda_identificacao": "DV: identificação",
    "mg_servico_reds": "mg.gov.br: serviço REDS",
}
PERFIS = [("desktop", COR_DESKTOP, "Computador"), ("mobile_4g", COR_MOBILE, "Celular 4G"),
          ("mobile_3g", "#7c2d12", "Celular 3G")]

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
    return f'<p class="pendente">Pendente: {esc(texto)} <strong>({esc(quem)})</strong></p>'


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
        ["RQ1", "A Delegacia Virtual é acessível?", "Qualidade do produto", "Automático pronto; teste manual pendente"],
        ["RQ2", "O sistema é rápido no celular?", "Qualidade do produto", "H2 confirmada"],
        ["RQ3", "O sistema é seguro?", "Qualidade do produto", "H3 confirmada"],
        ["RQ4", "Qual demanda ele atende e como ela mudou?", "Dados de operação", "Série SEJUSP pronta; LAI aguardando"],
        ["RQ5", "Quanto isso custa ao cidadão?", "Impacto", "Cenários com sensibilidade"],
    ]
    return secao("02", "perguntas", "Perguntas de pesquisa",
                 tabela(["", "Pergunta", "Caminho", "Situação"], linhas))


def sec_qualidade():
    lh = desempenho.carregar()
    desc = desempenho.descritiva(lh)
    testes = [desempenho.comparar(lh, "mobile_4g", "desktop"), desempenho.comparar(lh, "mobile_3g", "mobile_4g")]
    paginas = [p for p in NOMES_PAGINA if p in set(lh.pagina)]
    nomes = [NOMES_PAGINA[p] for p in paginas]

    f1 = go.Figure()
    for perfil, cor, rot in PERFIS:
        d = lh[lh.perfil == perfil]
        f1.add_box(x=[NOMES_PAGINA[p] for p in d.pagina], y=d.lcp_ms / 1000, name=rot, marker_color=cor,
                   boxpoints="all", jitter=.3, pointpos=0)
    f1.add_hline(y=2.5, line_dash="dash", line_color=COR_NEUTRA,
                 annotation_text="limite \"bom\" (2,5 s)", annotation_position="top left")
    f1.update_layout(title="RQ2: LCP por tela e perfil (5 rodadas cada)", yaxis_title="segundos", boxmode="group",
                     xaxis=dict(categoryorder="array", categoryarray=nomes))

    f2 = go.Figure()
    d = desc[desc.perfil == "mobile_4g"].set_index("pagina").reindex(paginas)
    f2.add_bar(x=nomes, y=d.acess_mediana, text=d.acess_mediana.astype(int), textposition="outside",
               marker_color=[COR_DESTAQUE if p.startswith("dv_") else COR_NEUTRA for p in paginas])
    f2.update_layout(title="RQ1: nota de acessibilidade (Lighthouse, 0–100)", yaxis_range=[0, 105], showlegend=False)

    viol = lh[lh.pagina.str.startswith("dv_")].violacoes_acessibilidade.dropna()
    ids = sorted({v for linha in viol for v in linha.split("|")})
    explic = {
        "color-contrast": "texto com pouco contraste: difícil de ler com baixa visão",
        "html-has-lang": "página sem idioma declarado: o leitor de tela pode ler com pronúncia errada",
        "image-alt": "imagens sem descrição: invisíveis para quem usa leitor de tela",
        "link-name": "links sem nome: o leitor de tela anuncia só \"link\"",
        "tabindex": "ordem de tabulação forçada: navegar pelo teclado fica confuso",
        "label": "campos de formulário sem rótulo: o leitor de tela não diz o que preencher",
        "button-name": "botões sem nome acessível",
        "select-name": "listas de seleção sem rótulo",
    }
    por_tela = {p: sorted({v for l in lh[lh.pagina == p].violacoes_acessibilidade.dropna() for v in l.split("|")})
                for p in paginas if p.startswith("dv_")}
    lista = "".join(f"<li><code>{esc(i)}</code>: {esc(explic.get(i, ''))} "
                    f"<em>({sum(i in v for v in por_tela.values())}/{len(por_tela)} telas)</em></li>" for i in ids)

    t = testes[0]
    kpis = '<div class="kpis">' + "".join([
        kpi(f"{t['razao_medianas']:.1f}×".replace(".", ","), "LCP no celular 4G ÷ computador",
            f"mediana {t['mediana_a']/1000:.1f} s × {t['mediana_b']/1000:.1f} s".replace(".", ",")),
        kpi(f"p = {t['p_valor']:.1g}", "Wilcoxon pareado (unilateral)", f"n = {t['n_pares']} pares, r = {t['r']}"),
        kpi(f"δ = {t['cliff_delta']:.2f}".replace(".", ","), "delta de Cliff", f"efeito {t['magnitude']}; {t['paginas_na_direcao']} telas"),
        kpi(f"{testes[1]['razao_medianas']:.1f}×".replace(".", ","), "3G ÷ 4G no celular", f"p = {testes[1]['p_valor']:.1g}"),
    ]) + "</div>"
    linhas = [[esc(NOMES_PAGINA[r.pagina]), esc(dict((a, c) for a, _, c in PERFIS)[r.perfil]),
               f"{r.lcp_mediana_ms/1000:.1f} s".replace(".", ","), f"{int(r.perf_mediana)}", f"{int(r.acess_mediana)}",
               f"{r.peso_kb_mediana:.0f} KB", "✅" if r.lcp_bom else "❌"]
              for r in desc.itertuples() if r.pagina in NOMES_PAGINA]

    ck = checklist_wcag.resumir(checklist_wcag.carregar())
    corpo = (kpis + f'<div class="grade2"><div>{fig_html(f1)}</div><div>{fig_html(f2)}</div></div>'
             "<p><strong>H2 confirmada:</strong> em todas as telas o celular é mais lento, com efeito grande. "
             "As telas da Delegacia Virtual ficam perto de 2 s no 4G, dentro do limite; as páginas do mg.gov.br "
             "que levam o cidadão até ela passam de 6 s no 4G e de 10 s no 3G.</p>"
             f"<h3>Barreiras automáticas nas telas da Delegacia Virtual (axe-core)</h3><ul>{lista}</ul>"
             "<details><summary>Tabela completa (medianas de 5 rodadas)</summary>"
             + tabela(["Tela", "Perfil", "LCP", "Perf.", "Acess.", "Peso", "LCP ≤ 2,5 s"], linhas) + "</details>")
    if ck["completo"]:
        corpo += (f"<p><strong>Teste manual:</strong> tarefa só com teclado: {'sim' if ck['tarefa_so_teclado'] else 'não'}. "
                  f"H1 {'confirmada' if ck['h1_todas_telas_falham'] else 'não confirmada'}.</p>")
    else:
        corpo += pendente(f"teste manual com teclado e VoiceOver (RQ1): {ck['progresso']} itens preenchidos", "Gabriel")
    return secao("03", "qualidade", "Qualidade do produto (RQ1 e RQ2)", corpo)


def sec_seguranca():
    r = an_seg.resumo_hosts()
    libs = an_seg.bibliotecas()
    dv = r[r.host.str.contains("delegaciavirtual")].iloc[0]
    kpis = '<div class="kpis">' + "".join([
        kpi(str(dv.n_cves), "CVEs conhecidas nas bibliotecas JS", "Delegacia Virtual"),
        kpi(f"{dv.n_cabecalhos_ausentes}/6", "cabeçalhos de segurança ausentes", "Delegacia Virtual"),
        kpi("TLS 1.0", "ainda aceito", "obsoleto desde 2021 (RFC 8996); sem TLS 1.3"),
    ]) + "</div>"
    ok = lambda b: "✅" if b else "❌"
    t1 = tabela(["Host", "CSP", "HSTS", "Sem TLS 1.0/1.1", "TLS 1.3", "Cabeçalhos ausentes"],
                [[esc(x.host), ok(x.tem_csp), ok(x.tem_hsts), ok(not x.aceita_tls_obsoleto), ok(x.aceita_tls1_3),
                  esc(x.cabecalhos_ausentes.replace("|", ", "))] for x in r.itertuples()])
    t2 = tabela(["Host", "Biblioteca", "Versão", "CVEs"],
                [[esc(x.host), esc(x.biblioteca), esc(x.versao), esc(x.cves.replace("|", ", ")) or "—"] for x in libs.itertuples()])
    corpo = (kpis + t1 + "<h3>Bibliotecas JavaScript carregadas</h3>" + t2 +
             "<p><strong>H3 confirmada:</strong> nenhum dos dois sites usa CSP, o mg.gov.br não usa HSTS e a Delegacia "
             "Virtual carrega jQuery 1.x, jQuery UI 1.10 e Bootstrap 4.0, todas com CVEs públicas (XSS).</p>"
             '<p class="aviso">Coleta só passiva (GET, como um navegador): mostra <em>exposição</em>, não uma falha '
             "explorada. Nenhum teste de intrusão foi feito.</p>")
    return secao("04", "seguranca", "Segurança (RQ3)", corpo)


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
    fl = impacto.lcp_fluxo()
    lcp_mob = fl["mobile_4g"]["soma_s"] / fl["mobile_4g"]["n_telas"]
    c = impacto.cenarios()
    corpo = f"""
<p>Quantas horas por ano os cidadãos passam esperando a Delegacia Virtual carregar no celular?
Ajuste as suposições: o resultado muda na hora.</p>
<div class="calc">
  <label>Registros online por ano <input id="c-reg" type="number" value="{REGISTROS_ANO_2020}" step="1000"></label>
  <label>Telas até concluir o boletim <input id="c-telas" type="number" value="{fl['mobile_4g']['n_telas']}" min="1" max="20"></label>
  <label>Segundos de espera por tela (celular) <input id="c-seg" type="number" value="{lcp_mob:.1f}" step="0.1"></label>
</div>
<div class="kpis"><div class="kpi grande"><div class="kpi-valor" id="c-res">–</div>
<div class="kpi-rot">horas por ano esperando a tela carregar</div><div class="kpi-nota" id="c-dias"></div></div></div>
<p class="aviso"><strong>O que não dá para afirmar:</strong> não sabemos a fração de acessos pelo celular,
as telas depois da identificação não foram medidas (exigem dados pessoais) e o tempo de preenchimento (o maior) fica
de fora. O valor padrão é a média do LCP mediano das 4 telas do fluxo no celular 4G.</p>
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
    f = go.Figure()
    for rede, cor in (("4g", COR_MOBILE), ("3g", "#7c2d12")):
        d = c[(c.rede_celular == rede) & (c.telas == fl["mobile_4g"]["n_telas"])]
        f.add_scatter(x=d.fracao_celular * 100, y=d.horas_ano, mode="lines+markers", name=f"celular {rede.upper()}",
                      line_color=cor)
    d = c[(c.rede_celular == "4g") & (c.telas == fl["mobile_4g"]["n_telas"])]
    f.add_scatter(x=d.fracao_celular * 100, y=d.horas_se_tudo_no_computador, mode="lines", name="se todos usassem computador",
                  line=dict(color=COR_DESKTOP, dash="dash"))
    f.update_layout(title="Sensibilidade: horas/ano de espera × fração de acessos no celular",
                    xaxis_title="% dos registros feitos no celular", yaxis_title="horas por ano")
    br = lambda n: f"{int(n):,}".replace(",", ".")
    corpo += (f"<h3>Cenários</h3>{fig_html(f)}"
              f"<p>Faixa de todos os 18 cenários (fração no celular 50–90%, 4G ou 3G, 4 a 8 telas): "
              f"<strong>{br(c.horas_ano.min())} a {br(c.horas_ano.max())} horas por ano</strong> só esperando as telas aparecerem.</p>"
              '<div class="kpis">' + kpi(f"≈ {impacto.populacao_def_visual_mg()/1000:.0f} mil", "pessoas com deficiência visual em MG",
                                        "estimativa: taxa nacional do Censo 2022 (3,9%) × população de MG") +
              kpi(f"{br(impacto.PCD_MG)}", "pessoas com deficiência em MG", "Censo 2022, qualquer tipo") + "</div>"
              "<p>Para esse público, as barreiras da RQ1 (imagens sem descrição, página sem idioma, links sem nome) "
              "pesam mais do que o tempo de carregamento.</p>")
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
