"""Cliente HTTP da API do GitHub: cache em disco, rate limit e backoff.

O GitHub impõe DOIS limites diferentes, e confundi-los derruba a coleta:

1. **Limite primário** — cota por hora (5.000 req/h no core com token). Quando
   zera, a resposta vem com `x-ratelimit-remaining: 0` e o momento da renovação
   em `x-ratelimit-reset`. Basta esperar até lá.
   A busca (`/search/*`) tem cota PRÓPRIA e muito menor (30 req/min), contada
   separadamente — por isso os limites são rastreados por recurso
   (`x-ratelimit-resource`) e não num contador único.

2. **Limite secundário** — proteção contra rajadas. Dispara mesmo com cota
   primária sobrando, quando as requisições vêm rápido demais. A resposta é
   403/429 com a cota primária intacta e a mensagem "secondary rate limit".
   Só esperar a cota não resolve: é preciso desacelerar.

Contra o limite secundário o cliente age de duas formas: um intervalo mínimo
entre requisições (prevenção — é o que evita o bloqueio acontecer) e, se mesmo
assim disparar, uma espera antes de repetir (remediação).
"""
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

# Ritmo entre requisições. O GitHub pede requisições em série e sem rajadas;
# estes valores mantêm a coleta bem abaixo do ponto em que o limite secundário
# dispara, ao custo de alguns minutos a mais numa coleta que leva horas.
MIN_INTERVAL = 0.75          # endpoints normais (core)
SEARCH_INTERVAL = 2.1        # /search/*: cota de 30/min => >= 2s entre chamadas
SECONDARY_LIMIT_WAIT = 60    # o GitHub pede "espere pelo menos um minuto"

# Mensagens que identificam o limite secundário no corpo da resposta 403.
_SECONDARY_MARKERS = ("secondary rate limit", "abuse detection", "rate limit")


class NotFoundError(Exception):
    """Recurso inexistente (404), por exemplo tag apagada."""


class GitHubClient:
    def __init__(self, token, cache_dir, *, opener=urlopen, sleep=time.sleep,
                 now=time.time, max_retries=5, base_url=BASE_URL,
                 min_interval=MIN_INTERVAL, search_interval=SEARCH_INTERVAL):
        self.token = token
        self.cache_dir = cache_dir
        self.base_url = base_url
        self.max_retries = max_retries
        self.min_interval = min_interval
        self.search_interval = search_interval
        self._opener = opener
        self._sleep = sleep
        self._now = now
        self._limits = {}          # recurso -> (restantes, reset_epoch)
        self._last_request = 0.0
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

    # ---- rate limit por recurso --------------------------------------
    @staticmethod
    def _resource_for(url):
        """Qual balde de cota a URL consome. /search tem cota própria (30/min)."""
        return "search" if "/search/" in url else "core"

    def _track(self, headers):
        """Guarda a cota informada pela resposta, separada por recurso."""
        if "x-ratelimit-remaining" not in headers:
            return
        resource = headers.get("x-ratelimit-resource", "core")
        try:
            self._limits[resource] = (int(headers["x-ratelimit-remaining"]),
                                      int(headers.get("x-ratelimit-reset", 0)))
        except ValueError:
            pass

    def _wait_for_quota(self, url):
        """Dorme até a cota primária daquele recurso renovar, se ela zerou."""
        resource = self._resource_for(url)
        remaining, reset = self._limits.get(resource, (None, None))
        if remaining == 0 and reset:
            wait = max(reset - self._now(), 0) + 1
            print(f"[http] cota '{resource}' esgotada: aguardando {wait:.0f} s",
                  file=sys.stderr, flush=True)
            self._sleep(wait)
            self._limits.pop(resource, None)

    # ---- ritmo (prevenção do limite secundário) ----------------------
    def _throttle(self, url):
        """Garante um intervalo mínimo desde a requisição anterior.

        É o que impede o limite secundário de disparar. Sem isso o cliente
        dispara requisições na velocidade da rede, que é justamente o padrão
        que o detector de rajadas do GitHub bloqueia."""
        interval = self.search_interval if self._resource_for(url) == "search" else self.min_interval
        if interval <= 0:
            return
        elapsed = self._now() - self._last_request
        if 0 <= elapsed < interval:
            self._sleep(interval - elapsed)
        self._last_request = self._now()

    # ---- rede, rate limit e retry ------------------------------------
    @staticmethod
    def _error_message(err):
        """Mensagem do corpo de um erro da API (identifica o limite secundário)."""
        try:
            return (json.loads(err.read()) or {}).get("message", "")
        except (ValueError, OSError, AttributeError):
            return ""

    def _request(self, url):
        attempt = 0
        while True:
            self._wait_for_quota(url)
            self._throttle(url)
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
                if err.code in (403, 429):
                    delay = self._rate_limit_delay(url, headers, err)
                    if delay is not None:
                        attempt += 1  # conta a tentativa: evita laço infinito num 403 teimoso
                        if attempt > self.max_retries:
                            raise RuntimeError(
                                f"rate limit persistente após {self.max_retries} esperas: {url}")
                        print(f"[http] rate limit: aguardando {delay:.0f} s "
                              f"(tentativa {attempt}/{self.max_retries})",
                              file=sys.stderr, flush=True)
                        self._sleep(delay)
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

    def _rate_limit_delay(self, url, headers, err):
        """Segundos a esperar por causa de rate limit, ou None se o 403/429 não
        for rate limit (aí é erro de verdade e deve propagar).

        Só calcula a espera; quem dorme é o chamador, para que a espera entre no
        mesmo orçamento de tentativas do backoff de 5xx.

        Ordem importa: `retry-after` é a instrução explícita do servidor; cota
        primária zerada tem hora certa para voltar; o resto é limite secundário,
        que exige desacelerar e não apenas esperar a cota."""
        if "retry-after" in headers:  # o servidor disse exatamente quanto esperar
            try:
                return int(headers["retry-after"]) + 1
            except ValueError:
                return SECONDARY_LIMIT_WAIT

        resource = self._resource_for(url)
        remaining, reset = self._limits.get(resource, (None, None))
        if remaining == 0:  # limite primário: espera a renovação da cota
            self._limits.pop(resource, None)
            return max(reset - self._now(), 0) + 1 if reset else SECONDARY_LIMIT_WAIT

        # Cota primária intacta num 403 => limite secundário (rajada).
        if any(marker in self._error_message(err).lower() for marker in _SECONDARY_MARKERS):
            self._slow_down()
            print(f"[http] limite secundário detectado: ritmo reduzido para "
                  f"{self.min_interval:.2f} s/req", file=sys.stderr, flush=True)
            return SECONDARY_LIMIT_WAIT

        return None  # 403 de verdade (token sem permissão, repo bloqueado...)

    def _slow_down(self):
        """Dobra o intervalo entre requisições após um limite secundário.

        Se o ritmo atual disparou o detector de rajadas, repetir no mesmo ritmo
        dispara de novo. O intervalo não volta a baixar durante a execução."""
        self.min_interval = max(self.min_interval * 2, 1.0)
        self.search_interval = max(self.search_interval * 2, 2.1)
