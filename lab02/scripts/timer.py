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

UM ARQUIVO POR PARTICIPANTE
---------------------------
Cada integrante edita o SEU proprio arquivo dentro da pasta do kata:

    katas/01_gastos_semanais/solution_mv.py   <- Marcus Vinicius
    katas/01_gastos_semanais/solution_gc.py   <- Gabriel Chagas
    katas/01_gastos_semanais/solution_gl.py   <- Guilherme Lana

Assim o codigo de cada trial fica identificado por quem o escreveu, e um
participante nao sobrescreve o trial do outro no mesmo kata.

O test_solution.py de cada kata faz `from solution import ...`, entao antes de
cada rodada de pytest o arquivo do participante e copiado por cima de
solution.py (que funciona como arquivo gerado, sempre restaurado ao stub no
fim do trial). Quem edita solution.py direto perde o trabalho na proxima
rodada de polling -- edite sempre o solution_<iniciais>.py.

Uso:
    python scripts/timer.py --kata 01_gastos_semanais --participant marcus --treatment ai
    python scripts/timer.py --kata 02_normalizador_tags --participant gabriel --treatment manual

Ctrl+C a qualquer momento aborta o trial sem gravar nada em disco.

Cada execucao acrescenta uma linha em data/trials.csv (uma linha por trial =
kata x participante x tratamento), a base de dados usada pela analise
estatistica da Sprint 3 (RQ1/RQ2). Ao final, o arquivo do participante e
copiado para data/trials/<trial_id>/solution_<iniciais>.py e o caminho vai
para a coluna solution_path -- e essa coluna que o script de metricas
estaticas (issue #31) percorre para a RQ3.

Se um trial for abortado no meio e voce quiser recomecar do zero:

    python scripts/timer.py --reset --kata 01_gastos_semanais --participant marcus
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

TIME_BOX_SECONDS = 35 * 60  # 2100s - fixo pelo enunciado, so pode ser reduzido, nunca aumentado
POLL_INTERVAL_SECONDS = 5
# Vocabulario alinhado com scripts/trial_plan.py, o plano oficial do grupo (issue #29).
TREATMENTS = ("ia_total", "manual")

# Iniciais usadas no nome do arquivo de cada integrante (ver desenho_experimental.md).
PARTICIPANT_INITIALS = {
    "marcusvv12": "mv",       # Marcus Vinicius
    "gabrielchagas13": "gc",  # Gabriel Chagas
    "gguilhermelana": "gl",   # Guilherme Lana
}

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LAB02_DIR = os.path.dirname(SCRIPT_DIR)
KATAS_DIR = os.path.join(LAB02_DIR, "katas")
STUBS_DIR = os.path.join(KATAS_DIR, "_stubs")  # copia canonica do enunciado vazio de cada kata
ARCHIVE_DIR = os.path.join(LAB02_DIR, "data", "trials")  # codigo final de cada trial, um subdir por trial_id
IMPORTED_FILE = "solution.py"  # nome que o test_solution.py importa; gerado a cada polling

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
    solution_path: str  # codigo final arquivado deste trial -- entrada da RQ3 (issue #31)


def initials_for(participant: str) -> str:
    """Iniciais do participante, usadas no nome do arquivo de solucao.

    Participante fora da tabela cai no proprio nome, para o script continuar
    utilizavel se o grupo mudar (ex.: um quarto integrante)."""
    return PARTICIPANT_INITIALS.get(participant.lower(), participant.lower())


def assert_in_plan(kata: str, participant: str, treatment: str) -> None:
    """Confere que (participante, kata, tratamento) e uma das 12 combinacoes do
    plano oficial de contrabalanceamento (scripts/trial_plan.py).

    Passar o --treatment errado e um erro de digitacao facil de cometer e que so
    aparece semanas depois, na analise: o Wilcoxon e pareado, entao um
    participante sem nenhum trial manual simplesmente nao entra na comparacao."""
    try:
        from trial_plan import TRIALS
    except ImportError:
        print("[timer] aviso: trial_plan.py nao encontrado -- validacao do plano pulada.")
        return

    planned = {(t.person, t.kata): t.treatment for t in TRIALS}.get((participant, kata))
    if planned is None:
        people = sorted({t.person for t in TRIALS})
        raise SystemExit(
            f"'{participant}' + '{kata}' nao consta no plano oficial (scripts/trial_plan.py). "
            f"Participantes validos: {', '.join(people)}"
        )
    if planned != treatment:
        raise SystemExit(
            f"TRATAMENTO ERRADO: pelo plano oficial, {participant} faz o {kata} em "
            f"'{planned}', nao em '{treatment}'. Ver scripts/trial_plan.py (issue #29)."
        )


def kata_dir(kata: str) -> str:
    path = os.path.join(KATAS_DIR, kata)
    if not os.path.isdir(path):
        available = ", ".join(sorted(k for k in os.listdir(KATAS_DIR) if not k.startswith("_")))
        raise SystemExit(f"Kata '{kata}' nao encontrado em {KATAS_DIR}. Disponiveis: {available}")
    return path


def stub_path(kata: str) -> str:
    path = os.path.join(STUBS_DIR, kata, IMPORTED_FILE)
    if not os.path.isfile(path):
        raise SystemExit(f"Stub original nao encontrado em {path} -- sem ele nao da pra iniciar um trial limpo.")
    return path


def solution_path_for(kata: str, participant: str) -> str:
    """katas/<kata>/solution_<iniciais>.py -- o arquivo que o participante edita."""
    return os.path.join(kata_dir(kata), f"solution_{initials_for(participant)}.py")


def read_text(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def prepare_solution_file(kata: str, participant: str) -> str:
    """Garante que o arquivo do participante exista e esteja no stub original.

    Comecar com codigo de um trial anterior mediria tempo de edicao, nao
    time-to-green -- e o dado iria pro CSV sem ninguem notar."""
    path = solution_path_for(kata, participant)
    if not os.path.isfile(path):
        shutil.copyfile(stub_path(kata), path)
        print(f"[timer] criado {os.path.basename(path)} a partir do stub.")
        return path

    if read_text(path) != read_text(stub_path(kata)):
        raise SystemExit(
            f"{os.path.basename(path)} nao esta no stub original -- provavelmente sobrou codigo de "
            f"outro trial seu neste kata. Rode: python scripts/timer.py --reset "
            f"--kata {kata} --participant {participant}"
        )
    return path


def reset_solution_file(kata: str, participant: str) -> None:
    """Devolve solution_<iniciais>.py ao stub original (trial abortado)."""
    path = solution_path_for(kata, participant)
    shutil.copyfile(stub_path(kata), path)
    restore_imported_file(kata)
    print(f"[timer] {os.path.basename(path)} restaurado ao stub original.")


def sync_imported_file(kata: str, participant: str) -> None:
    """Copia solution_<iniciais>.py por cima de solution.py, que e o modulo que
    o test_solution.py importa. Roda antes de cada rodada de pytest."""
    shutil.copyfile(solution_path_for(kata, participant), os.path.join(kata_dir(kata), IMPORTED_FILE))


def restore_imported_file(kata: str) -> None:
    """Devolve solution.py ao stub, pra nao deixar o repositorio sujo com um
    arquivo gerado nem vazar a solucao de um participante pro trial do outro."""
    shutil.copyfile(stub_path(kata), os.path.join(kata_dir(kata), IMPORTED_FILE))


def archive_solution(kata: str, participant: str, trial_id: str) -> str:
    """Copia o codigo final do trial pra data/trials/<trial_id>/ e retorna o
    caminho relativo a lab02/ (o que vai pro CSV)."""
    dest_dir = os.path.join(ARCHIVE_DIR, trial_id)
    os.makedirs(dest_dir, exist_ok=True)
    source = solution_path_for(kata, participant)
    dest = os.path.join(dest_dir, os.path.basename(source))
    shutil.copyfile(source, dest)
    return os.path.relpath(dest, LAB02_DIR).replace(os.sep, "/")


def run_pytest(kata: str, participant: str) -> tuple[int, int]:
    """Sincroniza o arquivo do participante e roda pytest no kata; retorna
    (testes_passando, testes_totais) a partir do resumo -q.

    Se o arquivo estiver com erro de sintaxe/coleta no meio da edicao (comum
    enquanto o participante ainda esta digitando), trata como 0 passando, 0
    total para essa leitura -- e transitorio, o polling seguinte corrige.
    """
    path = kata_dir(kata)
    sync_imported_file(kata, participant)
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--no-header", path],
        capture_output=True, text=True, cwd=path,
    )
    output = result.stdout + result.stderr
    passed = int(m.group(1)) if (m := PASSED_RE.search(output)) else 0
    failed = int(m.group(1)) if (m := FAILED_RE.search(output)) else 0
    errors = int(m.group(1)) if (m := ERROR_RE.search(output)) else 0
    return passed, passed + failed + errors


def collect_expected_total(kata: str, participant: str) -> int:
    """Total de testes esperado, coletado uma vez a partir do stub original
    (antes do participante comecar a editar) -- serve de denominador fixo
    para success_rate mesmo se uma edicao no meio do trial quebrar a coleta."""
    _, total = run_pytest(kata, participant)
    if total == 0:
        raise SystemExit(f"Nao foi possivel coletar nenhum teste em {kata} -- kata quebrado?")
    return total


def run_trial(kata: str, participant: str, treatment: str) -> TrialResult:
    assert_in_plan(kata, participant, treatment)
    solution_file = prepare_solution_file(kata, participant)
    expected_total = collect_expected_total(kata, participant)

    started_at = datetime.now(timezone.utc)
    start = time.monotonic()
    print(f"[timer] trial iniciado: kata={kata} participante={participant} tratamento={treatment}")
    print(f"[timer] EDITE: {os.path.relpath(solution_file, LAB02_DIR)}")
    print(f"[timer] time-box: {TIME_BOX_SECONDS}s ({TIME_BOX_SECONDS / 60:.0f} min) | testes esperados: {expected_total}")

    censored = True
    time_to_green: float | None = None
    n_passing = 0

    try:
        while True:
            elapsed = time.monotonic() - start
            if elapsed >= TIME_BOX_SECONDS:
                n_passing, _ = run_pytest(kata, participant)
                print(f"[timer] TIME-BOX ESGOTADO em {elapsed:.0f}s -- censurado em {TIME_BOX_SECONDS}s "
                      f"({n_passing}/{expected_total} testes passando)")
                break

            n_passing, _ = run_pytest(kata, participant)
            print(f"[timer] {elapsed:.0f}s -- {n_passing}/{expected_total} testes passando")

            if n_passing == expected_total:
                time_to_green = elapsed
                censored = False
                print(f"[timer] TODOS OS TESTES PASSARAM em {elapsed:.1f}s")
                break

            time.sleep(POLL_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        restore_imported_file(kata)
        print("\n[timer] trial abortado (Ctrl+C) -- nada foi salvo.")
        sys.exit(1)

    success_rate = round(n_passing / expected_total, 4)
    trial_id = f"{kata}_{participant}_{treatment}_{started_at.strftime('%Y%m%dT%H%M%S')}"

    archived = archive_solution(kata, participant, trial_id)
    restore_imported_file(kata)
    print(f"[timer] codigo final arquivado em {archived}")

    return TrialResult(
        trial_id=trial_id,
        participant=participant,
        kata=kata,
        treatment=treatment,
        started_at=started_at.isoformat(),
        time_to_green_seconds=round(time_to_green, 1) if time_to_green is not None else None,
        censored=censored,
        n_tests_passing=n_passing,
        n_tests_total=expected_total,
        success_rate=success_rate,
        solution_path=archived,
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
    parser.add_argument("--treatment", choices=TREATMENTS, help="'ai' (com assistente) ou 'manual' (sem)")
    parser.add_argument("--reset", action="store_true",
                        help="apenas restaura o arquivo do participante ao stub e sai (trial abortado)")
    parser.add_argument("--output", default=os.path.join(LAB02_DIR, "data", "trials.csv"), help="CSV de saida (append)")
    args = parser.parse_args()

    if args.reset:
        reset_solution_file(args.kata, args.participant)
        return

    if not args.treatment:
        parser.error("--treatment e obrigatorio (exceto com --reset)")

    trial = run_trial(args.kata, args.participant, args.treatment)
    append_csv(trial, args.output)

    print(f"[timer] trial salvo em {args.output}: {trial.trial_id}")
    print(f"[timer] time_to_green_seconds={trial.time_to_green_seconds} censored={trial.censored} "
          f"success_rate={trial.success_rate}")


if __name__ == "__main__":
    main()
