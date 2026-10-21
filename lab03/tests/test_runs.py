import json
from datetime import date

from pipeline.runs import collect_repo, collect_runs, month_ranges


def test_month_ranges_janela_de_12_meses():
    r = month_ranges(date(2025, 10, 1), date(2026, 9, 30))
    assert len(r) == 12
    assert r[0] == (date(2025, 10, 1), date(2025, 10, 31))
    assert r[3] == (date(2026, 1, 1), date(2026, 1, 31))
    assert r[4] == (date(2026, 2, 1), date(2026, 2, 28))
    assert r[-1] == (date(2026, 9, 1), date(2026, 9, 30))


def test_month_ranges_janela_parcial():
    assert month_ranges(date(2026, 1, 15), date(2026, 2, 10)) == [
        (date(2026, 1, 15), date(2026, 1, 31)), (date(2026, 2, 1), date(2026, 2, 10))]


def raw(i, **kw):
    return {"id": i, "workflow_id": 1, "name": "CI", "conclusion": "success",
            "created_at": "2026-01-01T00:00:00Z", "run_started_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:01:00Z", "extra": "x", **kw}


class FakeClient:
    """Simula a API: `total(lo, hi)` define total_count; `runs(lo, hi)` as runs."""
    def __init__(self, total, runs):
        self.total, self.runs = total, runs
        self.queries = []

    def _range(self, params):
        lo, hi = params["created"].split("..")
        return date.fromisoformat(lo), date.fromisoformat(hi)

    def get(self, path, params):
        lo, hi = self._range(params)
        self.queries.append((lo, hi))
        return {"total_count": self.total(lo, hi), "workflow_runs": []}, {}

    def get_pages(self, path, params):
        lo, hi = self._range(params)
        return [{"workflow_runs": self.runs(lo, hi)}]


def test_coleta_um_intervalo_por_mes_e_reduz_campos():
    client = FakeClient(lambda lo, hi: 1, lambda lo, hi: [raw(lo.month)])
    runs, stats = collect_runs(client, "o/r", "main", date(2026, 1, 1), date(2026, 3, 31))
    assert [r["id"] for r in runs] == [1, 2, 3]
    assert "extra" not in runs[0]
    assert stats == {"splits": 0, "capped_days": []}


def test_divide_intervalo_quando_atinge_teto_de_1000():
    # janeiro "estoura" o teto, mas cada metade não
    total = lambda lo, hi: 1000 if (hi - lo).days >= 20 else 10
    client = FakeClient(total, lambda lo, hi: [raw(lo.day * 100 + hi.day)])
    runs, stats = collect_runs(client, "o/r", "main", date(2026, 1, 1), date(2026, 1, 31))
    assert stats["splits"] == 1
    assert len(runs) == 2  # uma por metade, sem duplicar
    assert stats["capped_days"] == []


def test_dia_unico_acima_do_teto_e_registrado():
    client = FakeClient(lambda lo, hi: 1500, lambda lo, hi: [raw(1)])
    _, stats = collect_runs(client, "o/r", "main", date(2026, 1, 5), date(2026, 1, 5))
    assert stats["capped_days"] == ["2026-01-05"]


def test_remove_duplicatas_por_id():
    client = FakeClient(lambda lo, hi: 1, lambda lo, hi: [raw(7)])
    runs, _ = collect_runs(client, "o/r", "main", date(2026, 1, 1), date(2026, 2, 28))
    assert len(runs) == 1


def test_collect_repo_grava_e_retoma_sem_chamar_api(tmp_path):
    client = FakeClient(lambda lo, hi: 1, lambda lo, hi: [raw(1)])
    first = collect_repo(client, "o/r", "main", date(2026, 1, 1), date(2026, 1, 31), str(tmp_path))
    assert (tmp_path / "o__r.json").exists()
    n = len(client.queries)
    again = collect_repo(client, "o/r", "main", date(2026, 1, 1), date(2026, 1, 31), str(tmp_path))
    assert again == first and len(client.queries) == n
    assert json.loads((tmp_path / "o__r.json").read_text())["repo"] == "o/r"


# ---- paralelismo por intervalo mensal ----

def _cliente_12_meses():
    """Cada mês devolve uma run distinta, mais uma repetida entre meses."""
    def total(lo, hi):
        return 5

    def runs(lo, hi):
        return [raw(lo.month * 100), raw(999)]  # 999 aparece em todos os meses
    return FakeClient(total, runs)


def test_paralelo_devolve_o_mesmo_que_serial():
    """Paralelizar não pode mudar o dado coletado — só o tempo de coleta."""
    inicio, fim = date(2025, 10, 1), date(2026, 9, 30)
    serial, st_s = collect_runs(_cliente_12_meses(), "o/r", "main", inicio, fim, workers=1)
    paralelo, st_p = collect_runs(_cliente_12_meses(), "o/r", "main", inicio, fim, workers=4)
    assert serial == paralelo
    assert st_s == st_p


def test_paralelo_consulta_todos_os_meses():
    inicio, fim = date(2025, 10, 1), date(2026, 9, 30)
    cli = _cliente_12_meses()
    collect_runs(cli, "o/r", "main", inicio, fim, workers=4)
    assert len(set(cli.queries)) == 12


def test_stats_somam_corretamente_em_paralelo():
    """`splits` e `capped_days` são acumulados por thread e mesclados no fim;
    um dicionário compartilhado perderia incrementos."""
    inicio, fim = date(2026, 1, 1), date(2026, 3, 31)

    def total(lo, hi):
        return 1000 if lo == hi else 1000  # sempre no teto: força divisão até o dia

    cli = FakeClient(total, lambda lo, hi: [])
    _, st_serial = collect_runs(cli, "o/r", "main", inicio, fim, workers=1)
    cli2 = FakeClient(total, lambda lo, hi: [])
    _, st_par = collect_runs(cli2, "o/r", "main", inicio, fim, workers=4)
    assert st_serial["splits"] == st_par["splits"] > 0
    assert sorted(st_serial["capped_days"]) == sorted(st_par["capped_days"])


def test_campos_crus_sao_descartados_na_entrada():
    """O objeto cru da API (~8 KB) nao pode ser acumulado ate o fim da coleta.

    Guardar o cru e so filtrar em collect_runs fazia a memoria explodir em
    repositorios com centenas de milhares de runs (16 GB observados com 3
    threads). O filtro tem que acontecer assim que a pagina chega.
    """
    from pipeline.runs import KEEP_FIELDS, _fetch_range
    cli = FakeClient(lambda lo, hi: 2, lambda lo, hi: [raw(1), raw(2)])
    obtidos = _fetch_range(cli, "o/r", "main", date(2026, 1, 1), date(2026, 1, 31),
                           {"splits": 0, "capped_days": []})
    assert obtidos, "nenhuma run retornada"
    for run in obtidos:
        assert set(run) == set(KEEP_FIELDS)
        assert "extra" not in run


def test_runs_gravadas_mantem_apenas_os_campos_usados(tmp_path):
    cli = FakeClient(lambda lo, hi: 1, lambda lo, hi: [raw(lo.month)])
    runs, _ = collect_runs(cli, "o/r", "main", date(2026, 1, 1), date(2026, 3, 31), workers=3)
    from pipeline.runs import KEEP_FIELDS
    assert all(set(r) == set(KEEP_FIELDS) for r in runs)
