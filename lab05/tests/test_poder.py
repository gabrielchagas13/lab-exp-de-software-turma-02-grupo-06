import numpy as np
import pandas as pd
import pytest

from analise import poder


def test_menor_p_possivel_e_um_sobre_dois_elevado_a_k():
    assert poder.menor_p_possivel(3) == 0.125
    assert poder.menor_p_possivel(5) == pytest.approx(0.03125)


def test_estimar_piloto_com_uma_rodada_nao_tem_sigma_rodada(tmp_path):
    linhas = []
    for pag, m, d in [("a", 2000, 400), ("b", 7000, 1300), ("c", 6900, 1200)]:
        for disp, v in [("mobile", m), ("desktop", d)]:
            linhas.append({"pagina": pag, "dispositivo": disp, "lcp_ms": v})
    caminho = tmp_path / "r.csv"
    pd.DataFrame(linhas).to_csv(caminho, index=False)
    p = poder.estimar_piloto(str(caminho))
    assert p.n_telas == 3 and p.n_rodadas_min == 1
    assert np.isnan(p.sigma_rodada)
    assert p.delta == pytest.approx(np.mean(np.log([5, 7000 / 1300, 6900 / 1200])))


def test_sem_efeito_o_teste_rejeita_perto_de_alfa():
    rng = np.random.default_rng(1)
    p = poder.poder(rng, k=5, r=5, delta=0.0, sigma_tela=0.05,
                    sigma_rodada=0.1, repeticoes=1000)
    assert p["por_rodada"] < 0.10


def test_poder_cresce_com_rodadas_e_com_efeito():
    rng = np.random.default_rng(2)
    f = lambda r, d: poder.poder(rng, 5, r, d, 0.05, 0.3, 400)["por_rodada"]
    assert f(10, 0.223) > f(1, 0.223)
    assert f(5, 0.7) > f(5, 0.1)


def test_com_tres_telas_o_teste_por_tela_nunca_rejeita():
    rng = np.random.default_rng(3)
    p = poder.poder(rng, 3, 20, 2.0, 0.05, 0.05, 300)
    assert p["por_tela"] == 0.0


def test_parametros_invalidos():
    with pytest.raises(ValueError):
        poder.poder(np.random.default_rng(0), 1, 5, 0.2, 0.1, 0.1)
