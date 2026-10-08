"""Cliente HTTP da API do GitHub: cache em disco, rate limit e backoff."""
import hashlib
import json
import os
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_URL = "https://api.github.com"
_NEXT_RE = re.compile(r'<([^>]+)>;\s*rel="next"')


class NotFoundError(Exception):
    """Recurso inexistente (404), por exemplo tag apagada."""


class GitHubClient:
    def __init__(self, token, cache_dir, *, opener=urlopen, sleep=time.sleep,
                 now=time.time, max_retries=5, base_url=BASE_URL):
        self.token = token
        self.cache_dir = cache_dir
        self.base_url = base_url
        self.max_retries = max_retries
        self._opener = opener
        self._sleep = sleep
        self._now = now
        self._remaining = None
        self._reset = None
        os.makedirs(cache_dir, exist_ok=True)

    # ---- API pública -------------------------------------------------
    def build_url(self, path, params=None):
        url = self.base_url + path
        if params:
            url += "?" + urlencode(sorted(params.items()))
        return url

    def get(self, path, params=None):
        """GET com cache. Retorna (corpo_json, headers em minúsculas)."""
        return self._get_url(self.build_url(path, params))

    def get_pages(self, path, params=None):
        """Segue o header Link (rel="next") e retorna a lista de corpos."""
        url = self.build_url(path, params)
        pages = []
        while url:
            body, headers = self._get_url(url)
            pages.append(body)
            match = _NEXT_RE.search(headers.get("link", ""))
            url = match.group(1) if match else None
        return pages

    # ---- cache -------------------------------------------------------
    def _cache_path(self, url):
        return os.path.join(self.cache_dir, hashlib.sha1(url.encode()).hexdigest() + ".json")

    def _read_cache(self, url):
        try:
            with open(self._cache_path(url), encoding="utf-8") as f:
                entry = json.load(f)
            return entry["body"], entry["headers"]
        except (OSError, ValueError, KeyError):
            return None  # ausente ou corrompido (ex.: Ctrl+C no meio da escrita)

    def _write_cache(self, url, body, headers):
        path = self._cache_path(url)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"url": url, "headers": headers, "body": body}, f)
        os.replace(tmp, path)  # escrita atômica

    def _get_url(self, url):
        cached = self._read_cache(url)
        if cached is not None:
            return cached
        body, headers = self._request(url)
        self._write_cache(url, body, {"link": headers.get("link", "")})
        return body, headers

    # ---- rede, rate limit e retry ------------------------------------
    def _wait_for_quota(self):
        if self._remaining == 0 and self._reset:
            wait = max(self._reset - self._now(), 0) + 1
            print(f"[http] rate limit: aguardando {wait:.0f} s", file=sys.stderr, flush=True)
            self._sleep(wait)
            self._remaining = None

    def _track(self, headers):
        if "x-ratelimit-remaining" in headers:
            self._remaining = int(headers["x-ratelimit-remaining"])
            self._reset = int(headers.get("x-ratelimit-reset", 0))

    def _request(self, url):
        attempt = 0
        while True:
            self._wait_for_quota()
            req = Request(url, headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            })
            try:
                with self._opener(req, timeout=30) as resp:
                    headers = {k.lower(): v for k, v in resp.headers.items()}
                    body = json.loads(resp.read())
                self._track(headers)
                return body, headers
            except HTTPError as err:
                headers = {k.lower(): v for k, v in err.headers.items()}
                self._track(headers)
                if err.code in (403, 429) and self._handle_rate_limit(headers):
                    continue
                if err.code == 404:
                    raise NotFoundError(url) from err
                if err.code < 500:
                    raise
            except (URLError, TimeoutError, ConnectionError):
                pass
            attempt += 1  # 5xx ou falha de rede: backoff exponencial 1s, 2s, 4s...
            if attempt > self.max_retries:
                raise RuntimeError(f"falha após {self.max_retries} tentativas: {url}")
            self._sleep(2 ** (attempt - 1))

    def _handle_rate_limit(self, headers):
        """Espera a cota renovar. Retorna True se era rate limit."""
        if "retry-after" in headers:  # limite secundário
            self._sleep(int(headers["retry-after"]) + 1)
            return True
        if self._remaining == 0:
            self._wait_for_quota()
            return True
        return False
