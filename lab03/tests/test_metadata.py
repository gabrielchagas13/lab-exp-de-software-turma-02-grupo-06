import io
from datetime import date
from urllib.error import HTTPError

import pytest

from pipeline.metadata import age_years, collect_metadata, count_contributors, repo_metadata

END = date(2026, 9, 30)


class FakeClient:
    def __init__(self, body=(), link="", error=None):
        self.body, self.link, self.error = list(body), link, error
        self.calls = []

    def get(self, path, params=None):
        self.calls.append((path, params))
        if self.error:
            raise self.error
        return self.body, {"link": self.link}


def http_error(code):
    return HTTPError("http://x", code, "err", {}, io.BytesIO(b"{}"))


def item(**kw):
    return {"full_name": "o/r", "html_url": "https://github.com/o/r", "default_branch": "main",
            "stargazers_count": 1500, "forks_count": 30, "language": "Python",
            "created_at": "2020-09-30T12:00:00Z", **kw}


def test_contribuidores_le_ultima_pagina_do_link():
    link = ('<https://api.github.com/repositories/1/contributors?per_page=1&anon=true&page=2>; '
            'rel="next", <https://api.github.com/repositories/1/contributors?per_page=1&anon=true'
            '&page=347>; rel="last"')
    client = FakeClient([{"login": "a"}], link)
    assert count_contributors(client, "o/r") == 347
    assert client.calls == [("/repos/o/r/contributors", {"per_page": 1, "anon": "true"})]


@pytest.mark.parametrize("body,expected", [([{"login": "a"}], 1), ([], 0), (None, 0)])
def test_contribuidores_sem_link_conta_a_pagina(body, expected):
    client = FakeClient()
    client.body = body
    assert count_contributors(client, "o/r") == expected


def test_contribuidores_lista_grande_demais_retorna_none():
    assert count_contributors(FakeClient(error=http_error(403)), "o/r") is None


def test_contribuidores_outros_erros_sobem():
    with pytest.raises(HTTPError):
        count_contributors(FakeClient(error=http_error(500)), "o/r")


def test_idade_em_anos():
    assert age_years("2020-09-30T12:00:00Z", END) == 6.0
    assert age_years("2026-03-31T00:00:00Z", END) == 0.5


def test_repo_metadata_campos():
    m = repo_metadata(item(language=None), 12, END)
    assert m == {"full_name": "o/r", "html_url": "https://github.com/o/r",
                 "default_branch": "main", "stars": 1500, "forks": 30, "language": "",
                 "contributors": 12, "created_at": "2020-09-30T12:00:00Z", "age_years": 6.0}


def test_repo_metadata_sem_html_url():
    m = repo_metadata({k: v for k, v in item().items() if k != "html_url"}, 1, END)
    assert m["html_url"] == "https://github.com/o/r"


def test_collect_metadata_usa_contribuidores_da_api():
    m = collect_metadata(FakeClient([{"login": "a"}]), item(), END)
    assert m["contributors"] == 1 and m["stars"] == 1500
