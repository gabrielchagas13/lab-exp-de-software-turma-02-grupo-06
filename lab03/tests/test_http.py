import io
import json
from urllib.error import HTTPError, URLError

import pytest

from pipeline.http import GitHubClient, NotFoundError


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


def http_error(code, headers=None):
    return HTTPError("http://x", code, "err", headers or {}, io.BytesIO(b"{}"))


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


def make(tmp_path, *script, now=lambda: 1000):
    sleeps = []
    opener = FakeOpener(*script)
    client = GitHubClient("tok", str(tmp_path), opener=opener, sleep=sleeps.append, now=now)
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
