"""Testes do kappa de Fleiss e da consolidação do consenso (issue #66).

Os valores esperados de kappa são calculados à mão a partir da fórmula, não
copiados da saída do código — um teste que afirma o que o código já faz não
detecta erro nenhum.
"""
import pandas as pd
import pytest

from validacao.concordancia import (SEM_CONSENSO, consenso, executar,
                                    faixa_landis_koch, kappa_fleiss)


def rotulos(coluna, **por_avaliador):
    """{iniciais: DataFrame} a partir de {iniciais: [rótulos]}; itens = i0, i1, ..."""
    n = len(next(iter(por_avaliador.values())))
    return {inic: pd.DataFrame({"full_name": [f"i{i}" for i in range(n)], coluna: vals})
            for inic, vals in por_avaliador.items()}


# ---- kappa de Fleiss ------------------------------------------------------

def test_concordancia_perfeita_da_kappa_1():
    """2 itens, 3 avaliadores, 2 categorias, todos concordando.

    À mão: P_o = 1 (todos os itens unânimes). Cada categoria recebe 3 de 6
    votos, então p = 0,5 e P_e = 0,5² + 0,5² = 0,5.
    kappa = (1 - 0,5) / (1 - 0,5) = 1,0
    """
    rot = rotulos("corretiva", mv=["sim", "nao"], gc=["sim", "nao"], gl=["sim", "nao"])
    assert kappa_fleiss(rot, ["full_name"], "corretiva")["kappa"] == 1.0


def test_discordancia_total_da_kappa_negativo():
    """3 itens, 3 avaliadores, 3 categorias; em cada item sai uma de cada.

    À mão: P_i = (1²+1²+1² - 3) / (3·2) = 0 para todo item, logo P_o = 0.
    Cada categoria tem 3 de 9 votos: p = 1/3 e P_e = 3 · (1/3)² = 1/3.
    kappa = (0 - 1/3) / (1 - 1/3) = -0,5
    """
    rot = rotulos("tipo_projeto",
                  mv=["biblioteca", "aplicacao", "cli"],
                  gc=["aplicacao", "cli", "biblioteca"],
                  gl=["cli", "biblioteca", "aplicacao"])
    assert kappa_fleiss(rot, ["full_name"], "tipo_projeto")["kappa"] == -0.5


def test_kappa_alinha_pela_chave_e_nao_pela_ordem_das_linhas():
    """Se um avaliador entregar a planilha em outra ordem, o kappa não pode mudar."""
    base = rotulos("corretiva", mv=["sim", "nao"], gc=["sim", "nao"], gl=["sim", "nao"])
    base["gl"] = base["gl"].iloc[::-1].reset_index(drop=True)  # mesma resposta, ordem trocada
    assert kappa_fleiss(base, ["full_name"], "corretiva")["kappa"] == 1.0


def test_itens_em_branco_sao_descartados_e_contados():
    rot = rotulos("corretiva", mv=["sim", "nao", "sim"], gc=["sim", "nao", ""],
                  gl=["sim", "nao", "sim"])
    r = kappa_fleiss(rot, ["full_name"], "corretiva")
    assert r["n_itens"] == 2 and r["itens_descartados"] == 1


def test_sem_nenhum_item_rotulado_nao_quebra():
    rot = rotulos("corretiva", mv=["", ""], gc=["", ""], gl=["", ""])
    r = kappa_fleiss(rot, ["full_name"], "corretiva")
    assert r["kappa"] is None and r["n_itens"] == 0


@pytest.mark.parametrize("k,esperado", [
    (-0.1, "pobre"), (0.0, "leve"), (0.20, "leve"), (0.21, "razoável"),
    (0.40, "razoável"), (0.55, "moderada"), (0.75, "substancial"), (0.95, "quase perfeita"),
])
def test_faixas_de_landis_koch(k, esperado):
    assert faixa_landis_koch(k) == esperado


# ---- consenso -------------------------------------------------------------

def test_consenso_unanime_e_por_maioria():
    rot = rotulos("corretiva", mv=["sim", "sim"], gc=["sim", "nao"], gl=["sim", "sim"])
    df = consenso(rot, ["full_name"], "corretiva")
    assert list(df["corretiva"]) == ["sim", "sim"]        # 3-0 e 2-1
    assert list(df["unanime"]) == [True, False]


def test_empate_1_1_1_fica_sem_consenso():
    """Com 3 avaliadores e 3 respostas diferentes não há maioria: vai para reunião."""
    rot = rotulos("tipo_projeto", mv=["biblioteca"], gc=["aplicacao"], gl=["cli"])
    df = consenso(rot, ["full_name"], "tipo_projeto")
    assert df["tipo_projeto"].iloc[0] == SEM_CONSENSO
    assert not df["unanime"].iloc[0]


def test_consenso_preserva_o_voto_de_cada_avaliador():
    """A planilha de consenso precisa mostrar quem votou o quê, para a reunião
    de desempate e para auditoria depois."""
    rot = rotulos("corretiva", mv=["sim"], gc=["nao"], gl=["sim"])
    df = consenso(rot, ["full_name"], "corretiva")
    assert (df["mv"].iloc[0], df["gc"].iloc[0], df["gl"].iloc[0]) == ("sim", "nao", "sim")


# ---- execução completa ----------------------------------------------------

def _escrever_rotulos(dir_, inic, repos_rows, releases_rows):
    pd.DataFrame(repos_rows).to_csv(dir_ / f"rotulos_repos_{inic}.csv", index=False)
    pd.DataFrame(releases_rows).to_csv(dir_ / f"rotulos_releases_{inic}.csv", index=False)


def test_executar_gera_concordancia_e_consensos(tmp_path):
    rot_dir, out_dir = tmp_path / "rot", tmp_path / "out"
    rot_dir.mkdir()
    for inic in ("mv", "gc", "gl"):
        _escrever_rotulos(
            rot_dir, inic,
            [{"full_name": "o/r", "tipo_projeto": "biblioteca", "releases_sao_entregas": "sim"},
             {"full_name": "o/s", "tipo_projeto": "cli", "releases_sao_entregas": "nao"}],
            [{"full_name": "o/r", "tag": "v1", "corretiva": "nao"},
             {"full_name": "o/r", "tag": "v2", "corretiva": "sim"}])
    df = executar(str(rot_dir), str(out_dir))

    assert set(df["dimensao"]) == {"tipo_projeto", "releases_sao_entregas", "corretiva"}
    assert (df["kappa"] == 1.0).all()          # todos rotularam igual
    assert (df["n_avaliadores"] == 3).all()
    for nome in ("concordancia.csv", "consenso_tipo_projeto.csv",
                 "consenso_releases_sao_entregas.csv", "consenso_corretiva.csv"):
        assert (out_dir / nome).exists(), nome


def test_executar_exige_mais_de_um_avaliador(tmp_path):
    """Kappa com um avaliador só não existe; melhor falhar do que gravar lixo."""
    rot_dir, out_dir = tmp_path / "rot", tmp_path / "out"
    rot_dir.mkdir()
    _escrever_rotulos(rot_dir, "mv",
                      [{"full_name": "o/r", "tipo_projeto": "cli", "releases_sao_entregas": "sim"}],
                      [{"full_name": "o/r", "tag": "v1", "corretiva": "nao"}])
    with pytest.raises(SystemExit):
        executar(str(rot_dir), str(out_dir))
