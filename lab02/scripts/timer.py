"""
Cronometragem e coleta de tempo por trial (issue #28).

Mede o "time-to-green": tempo desde o inicio do trial ate o momento em que
todos os testes de aceitacao do kata passam (metrica primaria de RQ1, ver
hypotheses.py). Respeita o time-box fixo de 35 minutos (2100s) do enunciado
-- um trial que estoura o time-box e registrado como CENSURADO em 2100s, nao
descartado (descartar enviesaria a comparacao a favor do tratamento com mais
falhas).

Como funciona: dispara o cronometro e roda pytest no diretorio do kata a
cada POLL_INTERVAL_SECONDS, ate todos os testes passarem ou o time-box
esgotar. A deteccao e automatica (nao depende do participante lembrar de
apertar um botao "terminei"), o que remove uma fonte de erro humano de
medicao.

Uso:
    python scripts/timer.py --kata 01_gastos_semanais --participant marcus --treatment ai
    python scripts/timer.py --kata 02_normalizador_tags --participant gabriel --treatment manual

Ctrl+C a qualquer momento aborta o trial sem gravar nada em disco.

Cada execucao acrescenta uma linha em data/trials.csv (uma linha por trial =
kata x participante x tratamento), a base de dados usada pela analise
estatistica da Sprint 3 (RQ1/RQ2).
"""

import argparse
import csv
import os
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

TIME_BOX_SECONDS = 35 * 60  # 2100s - fixo pelo enunciado, so pode ser reduzido, nunca aumentado
POLL_INTERVAL_SECONDS = 5
TREATMENTS = ("ai", "manual")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LAB02_DIR = os.path.dirname(SCRIPT_DIR)
KATAS_DIR = os.path.join(LAB02_DIR, "katas")

PASSED_RE = re.compile(r"(\d+) passed")
FAILED_RE = re.compile(r"(\d+) failed")
ERROR_RE = re.compile(r"(\d+) error")


@dataclass
class TrialResult:
    trial_id: str
    participant: str
    kata: str
    treatment: str
    started_at: str
    time_to_green_seconds: float | None
    censored: bool
    n_tests_passing: int
    n_tests_total: int
    success_rate: float


def kata_dir(kata: str) -> str:
    path = os.path.join(KATAS_DIR, kata)
    if not os.path.isdir(path):
        available = ", ".join(sorted(os.listdir(KATAS_DIR)))
        raise SystemExit(f"Kata '{kata}' nao encontrado em {KATAS_DIR}. Disponiveis: {available}")
    return path


def run_pytest(path: str) -> tuple[int, int]:
    """Roda pytest no kata; retorna (testes_passando, testes_totais) a partir do resumo -q.

    Se o arquivo estiver com erro de sintaxe/coleta no meio da edicao (comum
    enquanto o participante ainda esta digitando), trata como 0 passando, 0
    total para essa leitura -- e transitorio, o polling seguinte corrige.
    """
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--no-header", path],
        capture_output=True, text=True, cwd=path,
    )
    output = result.stdout + result.stderr
    passed = int(m.group(1)) if (m := PASSED_RE.search(output)) else 0
    failed = int(m.group(1)) if (m := FAILED_RE.search(output)) else 0
    errors = int(m.group(1)) if (m := ERROR_RE.search(output)) else 0
    return passed, passed + failed + errors


def collect_expected_total(path: str) -> int:
    """Total de testes esperado, coletado uma vez a partir do stub original
    (antes do participante comecar a editar) -- serve de denominador fixo
    para success_rate mesmo se uma edicao no meio do trial quebrar a coleta."""
    _, total = run_pytest(path)
    if total == 0:
        raise SystemExit(f"Nao foi possivel coletar nenhum teste em {path} -- kata quebrado?")
    return total


def run_trial(kata: str, participant: str, treatment: str) -> TrialResult:
    path = kata_dir(kata)
    expected_total = collect_expected_total(path)

    started_at = datetime.now(timezone.utc)
    start = time.monotonic()
    print(f"[timer] trial iniciado: kata={kata} participante={participant} tratamento={treatment}")
    print(f"[timer] time-box: {TIME_BOX_SECONDS}s ({TIME_BOX_SECONDS / 60:.0f} min) | testes esperados: {expected_total}")

    censored = True
    time_to_green: float | None = None
    n_passing, n_total = 0, expected_total

    try:
        while True:
            elapsed = time.monotonic() - start
            if elapsed >= TIME_BOX_SECONDS:
                n_passing, n_total = run_pytest(path)
                n_total = expected_total
                print(f"[timer] TIME-BOX ESGOTADO em {elapsed:.0f}s -- censurado em {TIME_BOX_SECONDS}s "
                      f"({n_passing}/{expected_total} testes passando)")
                break

            n_passing, n_total = run_pytest(path)
            n_total = expected_total
            print(f"[timer] {elapsed:.0f}s -- {n_passing}/{expected_total} testes passando")

            if n_passing == expected_total:
                time_to_green = elapsed
                censored = False
                print(f"[timer] TODOS OS TESTES PASSARAM em {elapsed:.1f}s")
                break

            time.sleep(POLL_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("\n[timer] trial abortado (Ctrl+C) -- nada foi salvo.")
        sys.exit(1)

    success_rate = round(n_passing / expected_total, 4)
    trial_id = f"{kata}_{participant}_{treatment}_{started_at.strftime('%Y%m%dT%H%M%S')}"

    return TrialResult(
        trial_id=trial_id,
        participant=participant,
        kata=kata,
        treatment=treatment,
        started_at=started_at.isoformat(),
        time_to_green_seconds=round(time_to_green, 1) if time_to_green is not None else None,
        censored=censored,
        n_tests_passing=n_passing,
        n_tests_total=n_total,
        success_rate=success_rate,
    )


def append_csv(trial: TrialResult, output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    row = asdict(trial)
    file_exists = os.path.isfile(output_path)
    with open(output_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--kata", required=True, help="nome da pasta do kata (ex.: 01_gastos_semanais)")
    parser.add_argument("--participant", required=True, help="identificador do integrante (ex.: marcus)")
    parser.add_argument("--treatment", required=True, choices=TREATMENTS, help="'ai' (com assistente) ou 'manual' (sem)")
    parser.add_argument("--output", default=os.path.join(LAB02_DIR, "data", "trials.csv"), help="CSV de saida (append)")
    args = parser.parse_args()

    trial = run_trial(args.kata, args.participant, args.treatment)
    append_csv(trial, args.output)

    print(f"[timer] trial salvo em {args.output}: {trial.trial_id}")
    print(f"[timer] time_to_green_seconds={trial.time_to_green_seconds} censored={trial.censored} "
          f"success_rate={trial.success_rate}")


if __name__ == "__main__":
    main()
