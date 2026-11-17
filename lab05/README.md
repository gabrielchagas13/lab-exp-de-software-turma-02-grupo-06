# Lab 05: Delegacia Virtual de MG em produção

Experimento sobre um software real, em operação e de alto impacto: a **Delegacia Virtual da Polícia Civil de Minas Gerais**, que recebeu mais de 1,5 milhão de boletins online desde 2014.

**Pergunta:** a Delegacia Virtual atende bem, em acessibilidade, desempenho e disponibilidade, a demanda que absorveu? Quanto isso custa ao cidadão?

- Proposta completa (critérios, GQM, hipóteses, 7 categorias, ameaças, plano, piloto): [docs/proposta_s01.md](docs/proposta_s01.md)
- Mapa do fluxo "perda de documento": [docs/fluxo_perda_documento.md](docs/fluxo_perda_documento.md)
- Texto do pedido pela LAI: [docs/pedido_lai.md](docs/pedido_lai.md) e acompanhamento em [docs/protocolo_lai.md](docs/protocolo_lai.md)

## Requisitos
- Python 3.12+, Node.js 18+ e Google Chrome (para o Lighthouse)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

## Coleta
```bash
python -m coleta.disponibilidade   # 1 GET por página, ≥ 1 s entre elas
python -m coleta.lighthouse        # mobile + desktop, Lighthouse 13.6.0 fixado
python -m coleta.mapa_fluxo        # telas do fluxo perda de documento (GET apenas)
```
As páginas medidas ficam em `config.json`. Para o estudo longitudinal, agende com cron (a partir de `lab05/`):
```
*/15 * * * *    cd <caminho>/lab05 && .venv/bin/python -m coleta.disponibilidade
0 8,12,18,23 * * * cd <caminho>/lab05 && .venv/bin/python -m coleta.lighthouse
```

### Dados da SEJUSP (download manual)
O portal dados.mg.gov.br responde HTTP 403 para clientes automatizados, e nós respeitamos o bloqueio. Baixe pelo navegador o conjunto **"Dados abertos: ocorrências policiais"** da SEJUSP, salve em `data/sejusp/ocorrencias.csv` e rode:
```bash
python -m analise.perfil_sejusp
```

## Ética
Nenhum boletim é enviado (comunicação falsa de crime é crime, CP art. 340). Nenhum formulário é preenchido automaticamente, nenhum dado pessoal é coletado, e o limite é de 1 requisição/s. No mapeamento do fluxo a proibição está no código: `SessaoSomenteLeitura` recusa POST, e um teste automatizado verifica isso.

## Dados
| Arquivo | Conteúdo |
|---|---|
| `data/disponibilidade/checagens.csv` | timestamp, página, status HTTP, ok, tempo (s), bytes, erro |
| `data/lighthouse/resultados.csv` | notas (perf., acess., boas práticas, SEO), LCP, FCP, TBT, CLS, peso, violações de acessibilidade |
| `data/lighthouse/raw/` | JSON bruto do Lighthouse (não versionado: é grande) |
| `data/fluxo/telas.csv` | uma linha por tela do fluxo: título, campos, captcha, relógio de sessão, peso |
| `data/sejusp/` | CSV da SEJUSP baixado manualmente |

## Processo de desenvolvimento (2 semanas)

A semana 1 cobre as sprints Lab05S01 e Lab05S02, e a semana 2 cobre a Lab05S03 e a entrega final. Cada tarefa vira uma issue no GitHub Projects, e quem fecha a issue apresenta o bloco correspondente (regra do Lab04).

Papéis: **Gabriel Chagas** (A: planejamento, método e dashboard), **Marcus Vinicius** (B: instrumentação e coleta), **Guilherme Lana** (C: análise e impacto).

### Semana 1: proposta, coleta e análise (Lab05S01 + Lab05S02)
| Tarefa | Responsável | Código / artefato | Status |
|---|---|---|---|
| Proposta com as RQ1–RQ5, GQM, hipóteses e 7 categorias (1ª versão) | Gabriel Chagas | `docs/proposta_s01.md` | ✅ Pronto |
| Série mensal da SEJUSP: pandemia, sazonalidade, RMBH × interior (RQ4) | Gabriel Chagas | `analise/sejusp.py` | ✅ Pronto |
| Dashboard com as seções de todas as RQs | Gabriel Chagas | `dashboard/gerar.py` → `dashboard/index.html` | ✅ Pronto (seções de outros marcadas "em construção") |
| Protocolar o pedido LAI | Marcus Vinicius | `docs/pedido_lai.md`, `docs/protocolo_lai.md` | ✅ Protocolado em 17/11/2026 (nº 1510.000360/2026-61); prazo 07/12 |
| Teste manual com teclado e VoiceOver (RQ1) | Gabriel Chagas | `data/acessibilidade/checklist.csv` + `analise/checklist_wcag.py` | ⬜ A fazer |
| Mapear as telas do fluxo "perda de documento" até a revisão (sem enviar) | Marcus Vinicius | `coleta/mapa_fluxo.py`, `docs/fluxo_perda_documento.md`, `config.json` | ✅ Pronto (3 de 5 telas medíveis; 2 exigem mapeamento manual) |
| Lighthouse com 4G/3G e 5 rodadas por tela (RQ1, RQ2) | Marcus Vinicius | `coleta/lighthouse.py` | ⬜ A fazer |
| Coleta de segurança: cabeçalhos HTTP, TLS, bibliotecas JS (RQ3) | Marcus Vinicius | `coleta/seguranca.py` | ⬜ A fazer |
| Validação dos dados coletados | Marcus Vinicius | `coleta/validar.py` | ⬜ A fazer |
| Descritiva + Wilcoxon pareado celular × computador + tamanho do efeito (RQ2) | Guilherme Lana | `analise/desempenho.py` | ⬜ A fazer |
| Ameaças à validade (4 tipos) | Guilherme Lana | `docs/proposta_s01.md` §6 | ⬜ A fazer |

### Semana 2: impacto, conclusões e entrega (Lab05S03 + Final)
| Tarefa | Responsável | Código / artefato | Status |
|---|---|---|---|
| 7 categorias revisadas, conclusões e limitações | Gabriel Chagas | `docs/relatorio_final.md` | ⬜ A fazer |
| Resposta da LAI na série de demanda (se chegar) | Gabriel Chagas | `analise/lai.py` | ⬜ A fazer |
| Dashboard final (preencher as seções "em construção") | Gabriel Chagas | `dashboard/gerar.py` | ⬜ A fazer |
| Rodada final de coleta e pipeline de um comando | Marcus Vinicius | `run_all.sh` | ⬜ A fazer |
| Análise de segurança (RQ3) e testes automatizados | Marcus Vinicius | `analise/seguranca.py`, `tests/` | ⬜ A fazer |
| Impacto: horas de espera/ano e população com deficiência (RQ5) + sensibilidade | Guilherme Lana | `analise/impacto.py` | ⬜ A fazer |
| Roteiro da apresentação de 10 min | Todo o grupo | `docs/roteiro_apresentacao.md` | ⬜ A fazer |

### Dashboard
```bash
python -m dashboard.gerar   # gera dashboard/index.html a partir de data/
```
