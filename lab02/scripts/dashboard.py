#!/usr/bin/env python3
"""
Gera o dashboard de visualizacao (issue #49) a partir de data/trials.csv
(RQ1/RQ2, issue #28) e data/metrics.csv (RQ3, issue #31 +
scripts/aggregate_static_metrics.py).

Mostra estatistica DESCRITIVA (mediana/IQR) por tratamento -- o teste de
Wilcoxon pareado (RQ1/RQ2: issue #47; RQ3: issue #48) e feito a parte, sobre
os mesmos CSVs.

Roda de novo a qualquer momento (ex.: apos mais trials da Sprint 2 ou depois
de rodar aggregate_static_metrics.py) para atualizar lab02/dashboard.html.

Uso:
    python scripts/aggregate_static_metrics.py   # gera/atualiza data/metrics.csv
    python scripts/dashboard.py                  # gera/atualiza dashboard.html
"""

from __future__ import annotations

import csv
import json
import os
import statistics as stats

sys_path_here = os.path.dirname(os.path.abspath(__file__))
LAB02_DIR = os.path.dirname(sys_path_here)
TRIALS_CSV = os.path.join(LAB02_DIR, "data", "trials.csv")
METRICS_CSV = os.path.join(LAB02_DIR, "data", "metrics.csv")
OUTPUT_HTML = os.path.join(LAB02_DIR, "dashboard.html")

EXPECTED_TRIALS = 12  # 3 participantes x 4 katas (issue #29)
TREATMENT_LABEL = {"ia_total": "IA (geração integral)", "manual": "Manual"}
TREATMENT_ORDER = ["ia_total", "manual"]


def read_csv(path: str) -> list[dict]:
    if not os.path.isfile(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def to_float(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def iqr(values: list[float]) -> tuple[float, float]:
    if len(values) < 2:
        return (values[0], values[0]) if values else (0.0, 0.0)
    quantiles = stats.quantiles(values, n=4, method="inclusive")
    return quantiles[0], quantiles[2]


def summarize(values: list[float]) -> dict:
    if not values:
        return {"n": 0, "median": None, "q1": None, "q3": None}
    q1, q3 = iqr(values)
    return {"n": len(values), "median": round(stats.median(values), 2), "q1": round(q1, 2), "q3": round(q3, 2)}


def build_dataset(trials: list[dict], metrics: list[dict]) -> dict:
    metrics_by_id = {m["trial_id"]: m for m in metrics}

    rows = []
    for t in trials:
        m = metrics_by_id.get(t["trial_id"], {})
        rows.append({
            "trial_id": t["trial_id"],
            "participant": t["participant"],
            "kata": t["kata"],
            "treatment": t["treatment"],
            "time_to_green_seconds": to_float(t["time_to_green_seconds"]),
            "censored": t["censored"] == "True",
            "success_rate": to_float(t["success_rate"]),
            "n_tests_passing": int(t["n_tests_passing"]),
            "n_tests_total": int(t["n_tests_total"]),
            "loc": to_float(m.get("loc")),
            "cyclomatic_complexity_mean": to_float(m.get("cyclomatic_complexity_mean")),
            "duplication_pct": to_float(m.get("duplication_pct")),
        })

    by_treatment = {}
    for treatment in TREATMENT_ORDER:
        subset = [r for r in rows if r["treatment"] == treatment]
        by_treatment[treatment] = {
            "label": TREATMENT_LABEL[treatment],
            "time_to_green_seconds": summarize([r["time_to_green_seconds"] for r in subset if r["time_to_green_seconds"] is not None]),
            "success_rate": summarize([r["success_rate"] for r in subset if r["success_rate"] is not None]),
            "loc": summarize([r["loc"] for r in subset if r["loc"] is not None]),
            "cyclomatic_complexity_mean": summarize([r["cyclomatic_complexity_mean"] for r in subset if r["cyclomatic_complexity_mean"] is not None]),
            "duplication_pct": summarize([r["duplication_pct"] for r in subset if r["duplication_pct"] is not None]),
            "n_censored": sum(1 for r in subset if r["censored"]),
        }

    participants_done = sorted({r["participant"] for r in rows})
    missing = EXPECTED_TRIALS - len(rows)

    by_participant = []
    for participant in participants_done:
        prows = [r for r in rows if r["participant"] == participant]
        entry = {"participant": participant}
        for treatment in TREATMENT_ORDER:
            psub = [r for r in prows if r["treatment"] == treatment]
            times = [r["time_to_green_seconds"] for r in psub if r["time_to_green_seconds"] is not None]
            successes = [r["success_rate"] for r in psub if r["success_rate"] is not None]
            entry[treatment] = {
                "n": len(psub),
                "median_time": round(stats.median(times), 1) if times else None,
                "median_success": round(stats.median(successes), 2) if successes else None,
            }
        by_participant.append(entry)

    # normaliza RQ3 (0-1 por metrica, sobre o maior valor entre os dois tratamentos) para o radar
    rq3_keys = ["loc", "cyclomatic_complexity_mean", "duplication_pct"]
    rq3_max = {k: max((by_treatment[t][k]["median"] or 0) for t in TREATMENT_ORDER) or 1 for k in rq3_keys}
    radar = {
        t: [round((by_treatment[t][k]["median"] or 0) / rq3_max[k], 3) for k in rq3_keys]
        for t in TREATMENT_ORDER
    }

    return {
        "rows": rows,
        "by_treatment": by_treatment,
        "by_participant": by_participant,
        "radar": radar,
        "n_trials": len(rows),
        "n_expected": EXPECTED_TRIALS,
        "n_missing": missing,
        "n_with_metrics": sum(1 for r in rows if r["loc"] is not None),
        "participants_done": participants_done,
    }


def render_html(dataset: dict) -> str:
    data_json = json.dumps(dataset, ensure_ascii=False)
    generated_note = (
        f"{dataset['n_trials']}/{dataset['n_expected']} trials coletados"
        + (f" — faltam {dataset['n_missing']}" if dataset["n_missing"] > 0 else " — completo")
    )
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dashboard: LAB02 IA vs. Manual</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E%3Ctext y='13' font-size='14'%3E%F0%9F%93%8A%3C/text%3E%3C/svg%3E">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
<style>
  :root{{
    color-scheme: light;
    --surface-1:      #fcfcfb;
    --surface-2:      #ffffff;
    --page-plane:     #f4f3ef;
    --text-primary:   #0b0b0b;
    --text-secondary: #52514e;
    --text-muted:     #898781;
    --gridline:       #e1e0d9;
    --border:         rgba(11,11,11,0.10);
    --series-1:       #2a78d6;
    --series-1-soft:  #2a78d61a;
    --series-2:       #eb6834;
    --series-2-soft:  #eb68341a;
    --series-3:       #1baf7a;
    --accent-grad:    linear-gradient(135deg, #2a78d6 0%, #1baf7a 100%);
    --shadow:         0 1px 2px rgba(11,11,11,0.04), 0 8px 24px rgba(11,11,11,0.05);
  }}
  @media (prefers-color-scheme: dark){{
    :root:not([data-theme="light"]){{
      color-scheme: dark;
      --surface-1:      #17181a;
      --surface-2:      #1e1f22;
      --page-plane:     #0c0d0e;
      --text-primary:   #ffffff;
      --text-secondary: #c3c2b7;
      --text-muted:     #898781;
      --gridline:       #2c2c2a;
      --border:         rgba(255,255,255,0.10);
      --series-1:       #4a92f0;
      --series-1-soft:  #4a92f026;
      --series-2:       #f2793b;
      --series-2-soft:  #f2793b26;
      --series-3:       #24c98a;
      --shadow:         0 1px 2px rgba(0,0,0,0.3), 0 12px 28px rgba(0,0,0,0.35);
    }}
  }}
  :root[data-theme="dark"]{{
    color-scheme: dark;
    --surface-1:      #17181a;
    --surface-2:      #1e1f22;
    --page-plane:     #0c0d0e;
    --text-primary:   #ffffff;
    --text-secondary: #c3c2b7;
    --text-muted:     #898781;
    --gridline:       #2c2c2a;
    --border:         rgba(255,255,255,0.10);
    --series-1:       #4a92f0;
    --series-1-soft:  #4a92f026;
    --series-2:       #f2793b;
    --series-2-soft:  #f2793b26;
    --series-3:       #24c98a;
    --shadow:         0 1px 2px rgba(0,0,0,0.3), 0 12px 28px rgba(0,0,0,0.35);
  }}
  *{{ box-sizing:border-box; }}
  html,body{{ margin:0; padding:0; }}
  body{{
    background:var(--page-plane); color:var(--text-primary);
    font-family: system-ui, -apple-system, "Segoe UI", sans-serif; padding:24px;
  }}
  .wrap{{ max-width:1220px; margin:0 auto; }}
  header.top{{ display:flex; justify-content:space-between; align-items:flex-start; gap:16px; flex-wrap:wrap; }}
  header.top .hero{{ flex:1; min-width:280px; }}
  header.top .badge{{
    display:inline-block; font-size:11px; font-weight:700; letter-spacing:.04em; text-transform:uppercase;
    padding:4px 10px; border-radius:999px; margin-bottom:10px; color:#fff; background:var(--accent-grad);
  }}
  header.top h1{{ font-size:24px; margin:0 0 6px; letter-spacing:-.01em; }}
  header.top p{{ margin:0; color:var(--text-secondary); font-size:14px; max-width:720px; line-height:1.5; }}
  .theme-btn{{
    border:1px solid var(--border); background:var(--surface-1); color:var(--text-primary);
    border-radius:8px; padding:8px 14px; font-size:13px; cursor:pointer; box-shadow:var(--shadow);
  }}
  .theme-btn:hover{{ border-color: var(--series-1); }}
  .banner{{
    margin:16px 0 24px; padding:11px 16px; border-radius:10px; font-size:13px;
    background:var(--surface-1); border:1px solid var(--border); color:var(--text-secondary); box-shadow:var(--shadow);
  }}
  .banner.incomplete{{ border-color: var(--series-2); color: var(--series-2); background:var(--series-2-soft); }}
  .kpi-row{{
    display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
    gap:12px; margin-bottom:26px;
  }}
  .kpi{{
    background:var(--surface-1); border:1px solid var(--border); border-radius:14px; padding:16px 18px;
    box-shadow:var(--shadow); transition:transform .15s ease;
  }}
  .kpi:hover{{ transform:translateY(-2px); }}
  .kpi .label{{ font-size:11.5px; color:var(--text-secondary); margin-bottom:8px; text-transform:uppercase; letter-spacing:.03em; }}
  .kpi .value{{ font-size:26px; font-weight:700; font-variant-numeric:tabular-nums; letter-spacing:-.01em; }}
  .section-title{{ font-size:13px; font-weight:700; text-transform:uppercase; letter-spacing:.05em; color:var(--text-muted); margin:28px 2px 12px; }}
  .grid{{ display:grid; grid-template-columns:repeat(auto-fit,minmax(420px,1fr)); gap:16px; margin-bottom:16px; }}
  .card{{
    background:var(--surface-1); border:1px solid var(--border); border-radius:16px; padding:20px 22px 16px;
    box-shadow:var(--shadow);
  }}
  .card.full{{ grid-column:1 / -1; }}
  .card h2{{ font-size:15px; margin:0 0 4px; }}
  .card .metric-desc{{ font-size:12px; color:var(--text-muted); margin-bottom:14px; }}
  .hypo-box{{ margin-top:10px; padding:11px 13px; border-radius:10px; background:var(--page-plane); border:1px solid var(--border); font-size:12px; color:var(--text-secondary); line-height:1.55; }}
  .table-scroll{{ overflow-x:auto; border:1px solid var(--border); border-radius:14px; }}
  table.data-table{{ width:100%; border-collapse:collapse; font-size:12.5px; min-width:900px; }}
  table.data-table thead th{{
    text-align:left; padding:9px 12px; border-bottom:1px solid var(--border);
    color:var(--text-secondary); white-space:nowrap; font-weight:600; background:var(--surface-1);
  }}
  table.data-table tbody td{{ padding:8px 12px; border-bottom:1px solid var(--gridline); white-space:nowrap; font-variant-numeric:tabular-nums; }}
  table.data-table tbody tr:hover{{ background:var(--page-plane); }}
  .pill{{ display:inline-block; font-size:11px; padding:2px 9px; border-radius:999px; border:1px solid var(--border); font-weight:600; }}
  .pill.ia{{ color:var(--series-1); background:var(--series-1-soft); border-color:transparent; }}
  .pill.manual{{ color:var(--series-2); background:var(--series-2-soft); border-color:transparent; }}
  .pill.censored{{ color:var(--series-2); background:var(--series-2-soft); border-color:transparent; }}
  footer.page-foot{{ margin:32px 0 12px; font-size:12px; color:var(--text-muted); text-align:center; }}
  canvas{{ max-height:280px; }}

  .dumbbell{{ width:100%; height:auto; display:block; }}
  .dumbbell .row-label{{ fill:var(--text-secondary); font-size:12px; font-weight:600; }}
  .dumbbell .value-label{{ fill:var(--text-muted); font-size:10.5px; font-variant-numeric:tabular-nums; }}
  .dumbbell .connector{{ stroke:var(--gridline); stroke-width:3; stroke-linecap:round; }}
  .dumbbell .dot-ia{{ fill:var(--series-1); }}
  .dumbbell .dot-manual{{ fill:var(--series-2); }}
  .legend-row{{ display:flex; gap:18px; font-size:12px; color:var(--text-secondary); margin-bottom:6px; }}
  .legend-row .sw{{ display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:6px; vertical-align:-1px; }}
  .legend-row .sw.ia{{ background:var(--series-1); }}
  .legend-row .sw.manual{{ background:var(--series-2); }}
</style>
</head>
<body>
<div class="wrap">
  <header class="top">
    <div class="hero">
      <span class="badge">LAB02 · Experimento controlado</span>
      <h1>Geração integral por IA vs. codificação manual</h1>
      <p>Crossover within-subject (issue #29). Fonte: <code>data/trials.csv</code> (RQ1/RQ2) + <code>data/metrics.csv</code> (RQ3). Estatística descritiva (mediana/IQR) por tratamento — o teste de Wilcoxon pareado fica nas issues #47/#48.</p>
    </div>
    <button class="theme-btn" id="themeToggle" type="button">🌓 Alternar tema</button>
  </header>

  <div class="banner {'incomplete' if dataset['n_missing'] > 0 else ''}">{generated_note} · participantes com pelo menos 1 trial: {', '.join(dataset['participants_done']) or '—'} · trials com métricas estáticas (RQ3): {dataset['n_with_metrics']}/{dataset['n_trials']}</div>

  <div class="kpi-row" id="kpi-row"></div>

  <div class="section-title">Comparação pareada por participante (desenho within-subject)</div>
  <div class="grid">
    <div class="card">
      <h2>RQ1 — Time-to-green por participante</h2>
      <p class="metric-desc">Mediana de tempo (s) de cada integrante nos katas com IA vs. Manual — é exatamente essa diferença, por pessoa, que o Wilcoxon pareado (#47) testa.</p>
      <div class="legend-row"><span><span class="sw ia"></span>IA</span><span><span class="sw manual"></span>Manual</span></div>
      <svg class="dumbbell" id="dumbbell-time" viewBox="0 0 560 160"></svg>
    </div>
    <div class="card">
      <h2>RQ2 — Taxa de sucesso por participante</h2>
      <p class="metric-desc">Mediana de success_rate de cada integrante, mesmo pareamento.</p>
      <div class="legend-row"><span><span class="sw ia"></span>IA</span><span><span class="sw manual"></span>Manual</span></div>
      <svg class="dumbbell" id="dumbbell-success" viewBox="0 0 560 160"></svg>
    </div>
  </div>

  <div class="section-title">Métricas agregadas (todos os trials)</div>
  <div class="grid">
    <div class="card">
      <span class="pill ia">RQ1</span>
      <h2>Time-to-green (s)</h2>
      <p class="metric-desc">Geração + depuração até todos os testes passarem. Censurado em 2100s (35min) se o time-box estourar.</p>
      <canvas id="chart-time"></canvas>
      <div class="hypo-box" id="hypo-rq1"></div>
    </div>
    <div class="card">
      <span class="pill manual">RQ2</span>
      <h2>Taxa de sucesso dos testes</h2>
      <p class="metric-desc">% de testes de aceitação passando ao final do trial.</p>
      <canvas id="chart-success"></canvas>
      <div class="hypo-box" id="hypo-rq2"></div>
    </div>
    <div class="card">
      <span class="pill ia">RQ3</span>
      <h2>Perfil normalizado (LOC · CC · Duplicação)</h2>
      <p class="metric-desc">Cada eixo normalizado pelo maior valor entre os dois tratamentos (1.0 = quem "perde" naquela métrica) — dá pra ver de um golpe só onde a IA pesa mais.</p>
      <canvas id="chart-radar"></canvas>
    </div>
    <div class="card">
      <span class="pill manual">RQ3</span>
      <h2>LOC (controle)</h2>
      <p class="metric-desc">Linhas de código da solução final (Radon raw).</p>
      <canvas id="chart-loc"></canvas>
    </div>
    <div class="card">
      <span class="pill ia">RQ3</span>
      <h2>Complexidade ciclomática média</h2>
      <p class="metric-desc">Média por função/método (Radon cc).</p>
      <canvas id="chart-cc"></canvas>
    </div>
    <div class="card">
      <span class="pill manual">RQ3</span>
      <h2>Duplicação de código (%)</h2>
      <p class="metric-desc">Via jscpd sobre a solução final do trial.</p>
      <canvas id="chart-dup"></canvas>
      <div class="hypo-box" id="hypo-rq3"></div>
    </div>
  </div>

  <div class="card full">
    <h2>Trials individuais</h2>
    <div class="table-scroll">
      <table class="data-table">
        <thead>
          <tr>
            <th>Trial</th><th>Participante</th><th>Kata</th><th>Tratamento</th>
            <th>Tempo (s)</th><th>Sucesso</th><th>LOC</th><th>CC média</th><th>Duplicação %</th>
          </tr>
        </thead>
        <tbody id="trials-body"></tbody>
      </table>
    </div>
  </div>

  <footer class="page-foot">Gerado por <code>scripts/dashboard.py</code> a partir de <code>data/trials.csv</code> + <code>data/metrics.csv</code> — issue #49.</footer>
</div>

<script>
const DATA = {data_json};

function fmt(v, digits=1){{ return v === null || v === undefined ? '—' : Number(v).toFixed(digits); }}

function renderKpis(){{
  const el = document.getElementById('kpi-row');
  const items = [
    ['Trials coletados', `${{DATA.n_trials}}/${{DATA.n_expected}}`],
    ['Com métricas RQ3', `${{DATA.n_with_metrics}}`],
    ['Censurados (IA)', DATA.by_treatment.ia_total.n_censored],
    ['Censurados (Manual)', DATA.by_treatment.manual.n_censored],
  ];
  el.innerHTML = items.map(([label, value]) => `
    <div class="kpi"><div class="label">${{label}}</div><div class="value">${{value}}</div></div>
  `).join('');
}}

function renderHypoBox(id, rq, text){{
  document.getElementById(id).innerHTML = `<strong>${{rq}}</strong>: ${{text}}`;
}}

function medianBarChart(canvasId, metricKey, unitLabel){{
  const ia = DATA.by_treatment.ia_total[metricKey];
  const manual = DATA.by_treatment.manual[metricKey];
  new Chart(document.getElementById(canvasId), {{
    type: 'bar',
    data: {{
      labels: ['IA (geração integral)', 'Manual'],
      datasets: [{{
        label: `mediana ${{unitLabel}}`,
        data: [ia.median, manual.median],
        backgroundColor: ['#2a78d6', '#eb6834'],
        borderRadius: 8,
        borderSkipped: false,
        maxBarThickness: 90,
      }}]
    }},
    options: {{
      responsive: true,
      animation: {{ duration: 700, easing: 'easeOutQuart' }},
      plugins: {{
        legend: {{ display: false }},
        tooltip: {{
          callbacks: {{
            afterLabel: (ctx) => {{
              const s = ctx.dataIndex === 0 ? ia : manual;
              return `n=${{s.n}} · IQR [${{fmt(s.q1)}}, ${{fmt(s.q3)}}]`;
            }}
          }}
        }}
      }},
      scales: {{ y: {{ beginAtZero: true, grid: {{ color: 'rgba(128,128,128,.15)' }} }}, x: {{ grid: {{ display: false }} }} }}
    }}
  }});
}}

function radarChart(){{
  const labels = ['LOC', 'Complexidade ciclomática', 'Duplicação %'];
  new Chart(document.getElementById('chart-radar'), {{
    type: 'radar',
    data: {{
      labels,
      datasets: [
        {{
          label: 'IA (geração integral)',
          data: DATA.radar.ia_total,
          borderColor: '#2a78d6', backgroundColor: 'rgba(42,120,214,.18)',
          pointBackgroundColor: '#2a78d6', borderWidth: 2,
        }},
        {{
          label: 'Manual',
          data: DATA.radar.manual,
          borderColor: '#eb6834', backgroundColor: 'rgba(235,104,52,.18)',
          pointBackgroundColor: '#eb6834', borderWidth: 2,
        }},
      ]
    }},
    options: {{
      responsive: true,
      animation: {{ duration: 700, easing: 'easeOutQuart' }},
      plugins: {{ legend: {{ position: 'bottom', labels: {{ boxWidth: 10, font: {{ size: 11 }} }} }} }},
      scales: {{ r: {{ min: 0, max: 1, ticks: {{ display: false }}, grid: {{ color: 'rgba(128,128,128,.2)' }} }} }}
    }}
  }});
}}

function dumbbellChart(svgId, ia_key, manual_key, fmtDigits){{
  const svg = document.getElementById(svgId);
  const rows = DATA.by_participant;
  const W = 560, rowH = 40, padTop = 10, leftPad = 90, rightPad = 50;
  const H = padTop * 2 + rowH * rows.length;
  svg.setAttribute('viewBox', `0 0 ${{W}} ${{H}}`);

  const vals = [];
  rows.forEach(r => {{
    if (r.ia_total[ia_key] !== null) vals.push(r.ia_total[ia_key]);
    if (r.manual[manual_key] !== null) vals.push(r.manual[manual_key]);
  }});
  const min = Math.min(...vals, 0), max = Math.max(...vals, 1);
  const x = v => leftPad + (v - min) / (max - min || 1) * (W - leftPad - rightPad);

  let svgContent = '';
  rows.forEach((r, i) => {{
    const y = padTop + i * rowH + rowH / 2;
    const iaVal = r.ia_total[ia_key], manVal = r.manual[manual_key];
    svgContent += `<text class="row-label" x="4" y="${{y + 4}}">${{r.participant}}</text>`;
    if (iaVal !== null && manVal !== null){{
      svgContent += `<line class="connector" x1="${{x(iaVal)}}" y1="${{y}}" x2="${{x(manVal)}}" y2="${{y}}" />`;
    }}
    if (iaVal !== null){{
      svgContent += `<circle class="dot-ia" cx="${{x(iaVal)}}" cy="${{y}}" r="7" />`;
      svgContent += `<text class="value-label" x="${{x(iaVal)}}" y="${{y - 12}}" text-anchor="middle">${{iaVal.toFixed(fmtDigits)}}</text>`;
    }}
    if (manVal !== null){{
      svgContent += `<circle class="dot-manual" cx="${{x(manVal)}}" cy="${{y}}" r="7" />`;
      svgContent += `<text class="value-label" x="${{x(manVal)}}" y="${{y + 22}}" text-anchor="middle">${{manVal.toFixed(fmtDigits)}}</text>`;
    }}
  }});
  svg.innerHTML = svgContent;
}}

function renderTable(){{
  const body = document.getElementById('trials-body');
  body.innerHTML = DATA.rows.map(r => `
    <tr>
      <td>${{r.trial_id}}</td>
      <td>${{r.participant}}</td>
      <td>${{r.kata}}</td>
      <td><span class="pill ${{r.treatment === 'ia_total' ? 'ia' : 'manual'}}">${{r.treatment === 'ia_total' ? 'IA' : 'Manual'}}</span></td>
      <td>${{fmt(r.time_to_green_seconds)}}${{r.censored ? ' <span class="pill censored">censurado</span>' : ''}}</td>
      <td>${{fmt(r.success_rate, 2)}}</td>
      <td>${{fmt(r.loc, 0)}}</td>
      <td>${{fmt(r.cyclomatic_complexity_mean, 2)}}</td>
      <td>${{fmt(r.duplication_pct, 2)}}</td>
    </tr>
  `).join('');
}}

function initTheme(){{
  const btn = document.getElementById('themeToggle');
  btn.addEventListener('click', () => {{
    const cur = document.documentElement.getAttribute('data-theme');
    document.documentElement.setAttribute('data-theme', cur === 'dark' ? 'light' : 'dark');
  }});
}}

renderKpis();
medianBarChart('chart-time', 'time_to_green_seconds', 's');
medianBarChart('chart-success', 'success_rate', '');
medianBarChart('chart-loc', 'loc', 'linhas');
medianBarChart('chart-cc', 'cyclomatic_complexity_mean', '');
medianBarChart('chart-dup', 'duplication_pct', '%');
radarChart();
dumbbellChart('dumbbell-time', 'median_time', 'median_time', 0);
dumbbellChart('dumbbell-success', 'median_success', 'median_success', 2);
initTheme();
renderTable();

renderHypoBox('hypo-rq1', 'RQ1',
  `Mediana time-to-green: IA=${{fmt(DATA.by_treatment.ia_total.time_to_green_seconds.median)}}s vs. Manual=${{fmt(DATA.by_treatment.manual.time_to_green_seconds.median)}}s (descritivo — teste de Wilcoxon pareado na issue #47, exige amostra completa).`);
renderHypoBox('hypo-rq2', 'RQ2',
  `Mediana success_rate: IA=${{fmt(DATA.by_treatment.ia_total.success_rate.median, 2)}} vs. Manual=${{fmt(DATA.by_treatment.manual.success_rate.median, 2)}}.`);
renderHypoBox('hypo-rq3', 'RQ3',
  `Mediana duplicação: IA=${{fmt(DATA.by_treatment.ia_total.duplication_pct.median)}}% vs. Manual=${{fmt(DATA.by_treatment.manual.duplication_pct.median)}}% — LOC e CC nos gráficos ao lado (issue #48 traz o teste formal).`);
</script>
</body>
</html>
"""


def main() -> None:
    trials = read_csv(TRIALS_CSV)
    if not trials:
        raise SystemExit(f"{TRIALS_CSV} vazio ou nao encontrado -- rode os trials (scripts/timer.py) primeiro.")
    metrics = read_csv(METRICS_CSV)
    if not metrics:
        print(f"[dashboard] aviso: {METRICS_CSV} nao encontrado -- rode scripts/aggregate_static_metrics.py "
              f"antes para preencher RQ3 (LOC/CC/duplicação).")

    dataset = build_dataset(trials, metrics)
    html = render_html(dataset)

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[dashboard] {dataset['n_trials']}/{dataset['n_expected']} trials -> {OUTPUT_HTML}")


if __name__ == "__main__":
    main()
