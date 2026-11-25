#!/usr/bin/env bash
# Pipeline completo do Lab05: coleta → validação → análises → dashboard.
#   ./run_all.sh            # tudo (Lighthouse leva ~35 min)
#   ./run_all.sh --sem-coleta   # só reanalisa os dados já coletados
set -euo pipefail
cd "$(dirname "$0")"
PY=${PY:-.venv/bin/python}
if [[ "${1:-}" != "--sem-coleta" ]]; then
  $PY -m coleta.disponibilidade
  $PY -m coleta.seguranca
  $PY -m coleta.lighthouse
fi
$PY -m coleta.validar
$PY -m pytest -q
$PY -m analise.sejusp
$PY -m analise.desempenho
$PY -m analise.seguranca
$PY -m analise.impacto
$PY -m analise.checklist_wcag
$PY -m dashboard.gerar
