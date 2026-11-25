import pandas as pd

from analise.checklist_wcag import resumir
from analise.desempenho import cliff_delta, comparar
from coleta.lighthouse import flags_perfil
from coleta.seguranca import cves_de, detectar_bibliotecas, scripts_da_pagina
from coleta.validar import validar_lighthouse


def test_cves_jquery_antigo_e_bootstrap4():
    assert cves_de("jquery", "1.9.1") == ["CVE-2015-9251", "CVE-2019-11358", "CVE-2020-11022", "CVE-2020-11023"]
    assert cves_de("jquery", "3.7.1") == []
    assert cves_de("bootstrap", "4.0.0") == ["CVE-2018-14041", "CVE-2019-8331"]
    assert cves_de("bootstrap", "4.3.1") == []


def test_detecta_banner_e_ignora_scripts_de_ie():
    assert detectar_bibliotecas("/*! jQuery v1.11.1 | (c) */") == [("jquery", "1.11.1")]
    assert detectar_bibliotecas("/*! jQuery UI - v1.10.3 - 2013 */") == [("jquery-ui", "1.10.3")]
    html = '<script src="/a.js"></script><!--[if lt IE 9]><script src="/ie.js"></script><![endif]-->'
    assert scripts_da_pagina(html, "https://x.br/p/") == ["https://x.br/a.js"]


def test_flags_perfil():
    assert flags_perfil({"preset": "desktop"}) == ["--preset=desktop"]
    f = flags_perfil({"preset": "mobile", "rtt_ms": 300, "kbps": 700, "cpu": 4})
    assert "--throttling.rttMs=300" in f and "--throttling.throughputKbps=700" in f


def _lh(n_rep=5):
    linhas = []
    for pag in ["a", "b", "c"]:
        for rep in range(1, n_rep + 1):
            for perfil, lcp in [("mobile_4g", 3000 + rep), ("desktop", 800 + rep)]:
                linhas.append({"pagina": pag, "repeticao": rep, "perfil": perfil, "lcp_ms": lcp,
                               "dispositivo": perfil.split("_")[0], "rede": "4g" if "4g" in perfil else "cabo",
                               "erro": "", "cls": 0, **{c: 50 for c in ["nota_performance", "nota_acessibilidade",
                                                                       "nota_boas_praticas", "nota_seo"]},
                               **{c: 1 for c in ["fcp_ms", "tbt_ms", "speed_index_ms", "peso_total_kb"]}})
    return pd.DataFrame(linhas)


def test_wilcoxon_pareado_detecta_celular_mais_lento():
    r = comparar(_lh(), "mobile_4g", "desktop")
    assert r["n_pares"] == 15
    assert r["p_valor"] < 0.001
    assert r["cliff_delta"] == 1.0 and r["magnitude"] == "grande"
    assert r["paginas_na_direcao"] == "3/3"
    assert cliff_delta([1, 2], [1, 2]) == 0


def test_validar_aponta_repeticoes_faltando():
    assert validar_lighthouse(_lh(5)) == []
    erros = validar_lighthouse(_lh(3))
    assert any("3/5" in e for e in erros)


def test_checklist_h1():
    df = pd.DataFrame({"tela": ["t1", "t1", "t2"], "criterio_wcag": ["2.1.1", "1.1.1", "1.1.1"],
                       "resultado": ["passa", "falha", "falha"]})
    r = resumir(df)
    assert r["completo"] and r["h1_todas_telas_falham"] and r["tarefa_so_teclado"]
