import io
import json
from urllib.error import HTTPError, URLError

import pytest

from pipeline.http import SECONDARY_LIMIT_WAIT, GitHubClient, NotFoundError


class FakeResp:
    def __init__(self, body, headers=None):
        self._body = json.dumps(body).encode()
        self.headers = headers or {}

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def http_error(code, headers=None, message=""):
    body = json.dumps({"message": message} if message else {}).encode()
    return HTTPError("http://x", code, "err", headers or {}, io.BytesIO(body))


class FakeOpener:
    """Devolve respostas/erros em sequência e registra as URLs chamadas."""
    def __init__(self, *script):
        self.script = list(script)
        self.calls = []

    def __call__(self, req, timeout=None):
        self.calls.append(req.full_url)
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def make(tmp_path, *script, now=lambda: 1000, **kwargs):
    """Cliente de teste. O ritmo entre requisições vem desligado por padrão
    (min_interval=0) para que a lista `sleeps` contenha só as esperas de rate
    limit e backoff; os testes de ritmo o ligam explicitamente."""
    sleeps = []
    opener = FakeOpener(*script)
    kwargs.setdefault("min_interval", 0)
    kwargs.setdefault("search_interval", 0)
    client = GitHubClient("tok", str(tmp_path), opener=opener, sleep=sleeps.append,
                          now=now, **kwargs)
    return client, opener, sleeps


def test_cache_evita_segunda_chamada(tmp_path):
    client, opener, _ = make(tmp_path, FakeResp({"a": 1}))
    assert client.get("/x", {"p": 1})[0] == {"a": 1}
    assert client.get("/x", {"p": 1})[0] == {"a": 1}
    assert len(opener.calls) == 1


def test_cache_persiste_entre_instancias_retomada(tmp_path):
    make(tmp_path, FakeResp({"a": 1}))[0].get("/x")
    client2, opener2, _ = make(tmp_path)  # sem respostas: qualquer chamada falharia
    assert client2.get("/x")[0] == {"a": 1}
    assert opener2.calls == []


def test_cache_corrompido_e_refeito(tmp_path):
    client, opener, _ = make(tmp_path, FakeResp({"a": 1}), FakeResp({"a": 2}))
    client.get("/x")
    for f in tmp_path.iterdir():
        f.write_text("{corrompido")
    assert client.get("/x")[0] == {"a": 2}


def test_paginacao_segue_link_next(tmp_path):
    link = '<https://api.github.com/x?page=2>; rel="next", <https://api.github.com/x?page=2>; rel="last"'
    client, opener, _ = make(tmp_path, FakeResp([1], {"Link": link}), FakeResp([2]))
    assert client.get_pages("/x") == [[1], [2]]
    assert opener.calls[1] == "https://api.github.com/x?page=2"


def test_backoff_exponencial_em_5xx(tmp_path):
    client, _, sleeps = make(tmp_path, http_error(500), http_error(502), http_error(503), FakeResp({"ok": 1}))
    assert client.get("/x")[0] == {"ok": 1}
    assert sleeps == [1, 2, 4]


def test_backoff_em_erro_de_rede(tmp_path):
    client, _, sleeps = make(tmp_path, URLError("down"), FakeResp({"ok": 1}))
    assert client.get("/x")[0] == {"ok": 1}
    assert sleeps == [1]


def test_desiste_apos_max_tentativas(tmp_path):
    client, _, sleeps = make(tmp_path, *[http_error(500)] * 6)
    with pytest.raises(RuntimeError):
        client.get("/x")
    assert sleeps == [1, 2, 4, 8, 16]


def test_404_levanta_not_found_sem_retry(tmp_path):
    client, opener, sleeps = make(tmp_path, http_error(404))
    with pytest.raises(NotFoundError):
        client.get("/x")
    assert sleeps == [] and len(opener.calls) == 1


def test_outro_4xx_propaga(tmp_path):
    client, _, _ = make(tmp_path, http_error(401))
    with pytest.raises(HTTPError):
        client.get("/x")


def test_espera_reset_quando_cota_zera(tmp_path):
    headers = {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1060"}
    client, _, sleeps = make(tmp_path, FakeResp({"a": 1}, headers), FakeResp({"b": 2}), now=lambda: 1000)
    client.get("/x")
    client.get("/y")
    assert sleeps == [61]  # 1060 - 1000 + 1


def test_403_com_rate_limit_espera_e_repete(tmp_path):
    headers = {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1010"}
    client, opener, sleeps = make(tmp_path, http_error(403, headers), FakeResp({"ok": 1}))
    assert client.get("/x")[0] == {"ok": 1}
    assert sleeps == [11] and len(opener.calls) == 2


def test_retry_after_do_limite_secundario(tmp_path):
    client, _, sleeps = make(tmp_path, http_error(429, {"Retry-After": "30"}), FakeResp({"ok": 1}))
    assert client.get("/x")[0] == {"ok": 1}
    assert sleeps == [31]


def test_403_sem_rate_limit_propaga(tmp_path):
    client, _, _ = make(tmp_path, http_error(403, {"X-RateLimit-Remaining": "50"}))
    with pytest.raises(HTTPError):
        client.get("/x")


# ---- limite secundário (cota primária intacta, requisições rápidas demais) ----

SECONDARY_MSG = ("You have exceeded a secondary rate limit. "
                 "Please wait a few minutes before you try again.")


def test_limite_secundario_espera_e_repete(tmp_path):
    """403 com cota primária sobrando é limite secundário: espera, não falha."""
    client, opener, sleeps = make(
        tmp_path,
        http_error(403, {"X-RateLimit-Remaining": "4500"}, SECONDARY_MSG),
        FakeResp({"ok": 1}))
    assert client.get("/x")[0] == {"ok": 1}
    assert sleeps == [60] and len(opener.calls) == 2


def test_limite_secundario_reduz_o_ritmo(tmp_path):
    """Repetir no mesmo ritmo dispara o limite de novo, então o ritmo cai."""
    client, _, _ = make(
        tmp_path,
        http_error(403, {"X-RateLimit-Remaining": "4500"}, SECONDARY_MSG),
        FakeResp({"ok": 1}),
        min_interval=0.75, search_interval=2.1, now=lambda: 1000)
    client.get("/x")
    assert client.min_interval == 1.5


def test_limite_secundario_nao_entra_em_laco_infinito(tmp_path):
    """403 de rate limit que nunca cede desiste depois de max_retries."""
    # erros distintos: o corpo de um HTTPError só pode ser lido uma vez
    client, _, sleeps = make(
        tmp_path,
        *[http_error(403, {"X-RateLimit-Remaining": "4500"}, SECONDARY_MSG) for _ in range(8)])
    with pytest.raises(RuntimeError):
        client.get("/x")
    # 5 esperas de rate limit (= max_retries) e não um laço infinito; as demais
    # entradas em `sleeps` são o intervalo entre requisições, que o _slow_down
    # passou a aplicar depois do primeiro bloqueio.
    assert sleeps.count(SECONDARY_LIMIT_WAIT) == 5


def test_403_de_permissao_continua_propagando(tmp_path):
    """403 sem mensagem de rate limit é erro real e não deve virar espera."""
    client, _, sleeps = make(
        tmp_path, http_error(403, {"X-RateLimit-Remaining": "4500"}, "Must have admin rights"))
    with pytest.raises(HTTPError):
        client.get("/x")
    assert sleeps == []


# ---- cotas separadas: /search tem 30/min, o core tem 5000/h ----

def test_cota_de_busca_nao_bloqueia_o_core(tmp_path):
    """Zerar a busca não pode fazer o cliente esperar em endpoints normais."""
    esgotada = {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1060",
                "X-RateLimit-Resource": "search"}
    client, _, sleeps = make(tmp_path, FakeResp({"items": []}, esgotada), FakeResp({"a": 1}),
                             now=lambda: 1000)
    client.get("/search/repositories", {"q": "x"})
    client.get("/repos/o/r")  # recurso 'core': cota intacta, não espera
    assert sleeps == []


def test_cota_de_busca_esgotada_espera_na_proxima_busca(tmp_path):
    esgotada = {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1060",
                "X-RateLimit-Resource": "search"}
    client, _, sleeps = make(tmp_path, FakeResp({"items": []}, esgotada), FakeResp({"items": [1]}),
                             now=lambda: 1000)
    client.get("/search/repositories", {"q": "a"})
    client.get("/search/repositories", {"q": "b"})
    assert sleeps == [61]


# ---- ritmo entre requisições (prevenção) ----

def test_ritmo_minimo_entre_requisicoes(tmp_path):
    """Sem intervalo o cliente dispara rajadas, que é o que causa o bloqueio."""
    relogio = [1000.0]
    client, _, sleeps = make(tmp_path, FakeResp({"a": 1}), FakeResp({"b": 2}),
                             now=lambda: relogio[0], min_interval=0.75)
    client.get("/x")
    relogio[0] += 0.25          # passou só 0,25s desde a requisição anterior
    client.get("/y")
    assert sleeps == [0.5]      # completa os 0,75s


def test_busca_usa_intervalo_maior_que_o_core(tmp_path):
    client, _, sleeps = make(tmp_path, FakeResp({"items": []}),
                             now=lambda: 1000, min_interval=0.75, search_interval=2.1)
    client._last_request = 1000.0   # requisição imediatamente anterior
    client.get("/search/repositories", {"q": "x"})
    assert sleeps == [2.1]
