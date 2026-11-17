from coleta.lighthouse import resumir


def test_resumir_extrai_notas_metricas_e_violacoes():
    rel = {
        "categories": {
            "performance": {"score": 0.42},
            "accessibility": {"score": 0.8, "auditRefs": [
                {"id": "color-contrast", "weight": 7},
                {"id": "image-alt", "weight": 10},
                {"id": "manual", "weight": 0},
            ]},
        },
        "audits": {
            "largest-contentful-paint": {"numericValue": 5321.4},
            "total-byte-weight": {"numericValue": 2048},
            "color-contrast": {"score": 0},
            "image-alt": {"score": 1},
            "manual": {"score": 0},
        },
    }
    r = resumir(rel)
    assert r["nota_performance"] == 42
    assert r["nota_acessibilidade"] == 80
    assert r["nota_seo"] == ""
    assert r["lcp_ms"] == 5321.4
    assert r["peso_total_kb"] == 2.0
    assert r["violacoes_acessibilidade"] == "color-contrast"
