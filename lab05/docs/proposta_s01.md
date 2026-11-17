# Lab05S01: Proposta

**Software:** Delegacia Virtual da Polícia Civil de Minas Gerais (registro de ocorrência online, integrado ao REDS/SIDS)
**Pergunta de pesquisa:** A Delegacia Virtual de MG atende bem, em acessibilidade, desempenho e disponibilidade, a demanda que absorveu desde 2014? Quanto isso custa ao cidadão?

## 1. Os três critérios

| Critério | Evidência | Fonte (acesso em 17/11/2026) |
|---|---|---|
| Real | Sistema oficial da PCMG, em `delegaciavirtual.sids.mg.gov.br`, listado como serviço no portal mg.gov.br | [mg.gov.br: Registrar ocorrência (Reds)](https://www.mg.gov.br/servico/registrar-ocorrencia-policial-reds) |
| Em operação | No ar desde 30/04/2014. Respondeu HTTP 200 no piloto de 17/11/2026. O registro online tem a mesma validade do presencial | idem; piloto em `data/disponibilidade/checagens.csv` |
| Alto impacto | 1.099.340 registros em 5 anos (2014–2019); 205,8 mil de jan. a nov. de 2020; mais de 1,5 milhão até abril de 2021. "Perda de documentos" foi ~68% dos registros | [Tribuna de Minas, 30/04/2021](https://tribunademinas.com.br/noticias/minas/30-04-2021/delegacia-virtual-da-pcmg-tem-mais-de-15-milhao-de-registros-em-sete-anos.html?amp=1); [Agência Minas](https://www.agenciaminas.mg.gov.br/noticia/policia-civil-incentiva-uso-da-delegacia-virtual-107798) |

Os números de impacto mais recentes serão pedidos via LAI (`docs/pedido_lai.md`).

## 2. Caminhos escolhidos (combinados)
1. **Avaliar a qualidade do produto (ISO/IEC 25010):** acessibilidade (WCAG 2.1 AA), eficiência de desempenho e segurança, medidas de fora em cada tela do fluxo "perda de documento" até a revisão, sem enviar.
2. **Analisar dados de operação:** números de uso da Delegacia Virtual (imprensa, PCMG, LAI) e a série mensal da SEJUSP-MG (2012–2026) como demanda potencial. Esse caminho alimenta o impacto (seção 5 do enunciado).

A coleta contínua a cada 15 min foi retirada: depende de uma máquina ligada por semanas. A disponibilidade aparece só como limitação.

## 3. GQM
**Objetivo (template de Basili):** *Analisar* a Delegacia Virtual de MG *com o propósito de* avaliar *com respeito à* acessibilidade, desempenho, segurança e demanda atendida, *do ponto de vista do* cidadão mineiro, *no contexto de* acesso público pela internet em 2026.

| Pergunta | Métricas | Escala |
|---|---|---|
| RQ1. A Delegacia Virtual é acessível? | M1 nota de acessibilidade (0–100); M2 nº e tipos de violações WCAG por tela; M3 conclusão da tarefa só com teclado / leitor de tela (sim/não) | M1 ordinal*; M2 razão / nominal; M3 nominal |
| RQ2. O sistema é rápido no celular? | M4 LCP (ms) em 4G e 3G; M5 peso da página (KB); M6 nota de performance | M4, M5 razão; M6 ordinal* |
| RQ3. O sistema é seguro? | M7 nota SSL Labs (A–F); M8 cabeçalhos de segurança ausentes; M9 bibliotecas JS com CVE conhecida | M7 ordinal; M8, M9 razão |
| RQ4. Que demanda ele atende e como ela mudou? | M10 registros online/ano (imprensa, LAI); M11 ocorrências/mês (SEJUSP); M12 desvio sazonal (%) | razão |
| RQ5. Quanto isso custa ao cidadão? | M13 horas de espera/ano = registros × telas × LCP (derivada); M14 população com deficiência visual em MG (IBGE) | razão |

\*A nota do Lighthouse é uma média ponderada de pontuações; nos testes ela é tratada como ordinal, com testes não paramétricos.

## 4. Hipóteses
- **H1 (RQ1):** a Delegacia Virtual não atende à WCAG 2.1 AA (≥ 1 violação de nível A ou AA em toda tela do fluxo).
- **H2 (RQ2):** LCP no celular > LCP no computador. H0: distribuições iguais. Teste: Wilcoxon pareado por tela. Efeito: r e delta de Cliff.
- **H3 (RQ3):** faltam cabeçalhos de segurança recomendados (CSP, HSTS) e há bibliotecas JS com CVE conhecida.
- **H4 (RQ4):** houve queda nas ocorrências no isolamento (abr–jul/2020) e a sazonalidade é fraca (< 10%). Resultado parcial: queda de 32% contra o mesmo período de 2019 e sazonalidade máxima de ±5% (`analise/sejusp.py`).

## 5. As 7 categorias da pesquisa (1ª versão)
| Categoria | Classificação | Justificativa |
|---|---|---|
| Natureza | Aplicada | Gera recomendações para um serviço público em uso |
| Objetivos | Descritiva e explicativa | Descreve a qualidade e a demanda; testa hipóteses de diferença (mobile × desktop, horário) |
| Abordagem | Quantitativa | Métricas numéricas e testes estatísticos |
| Procedimentos | Levantamento de campo (medição) + documental (dados abertos, LAI) | Mede o sistema em produção e analisa registros oficiais |
| Tempo | Transversal (medição do sistema) + longitudinal (série SEJUSP 2012–2026) | O sistema é medido numa janela curta; a demanda é analisada ao longo de 14 anos |
| Controle | Observacional, com parte quase-experimental | Não controlamos o sistema. Mobile × desktop é manipulado na medição, mas sem aleatorizar o servidor. A série interrompida é quase-experimento |
| Nível de evidência | Moderado | Correlacional e quase-experimental; não permite causalidade forte |

## 6. Ameaças à validade (1ª versão)
- **Conclusão:** notas do Lighthouse variam entre execuções. *Mitigação:* repetições em vários horários, testes não paramétricos, tamanho do efeito.
- **Interna:** a rede e a máquina do grupo influenciam o tempo. *Mitigação:* mesma máquina e rede, throttling simulado do Lighthouse, registro do horário.
- **Construto:** a nota automática não é igual à experiência real; o axe detecta só parte dos problemas de WCAG (*Goodhart*: um site pode "jogar" a nota). *Mitigação:* olhar as violações concretas e, se der, fazer o estudo com pessoas.
- **Externa:** resultado vale para MG e para as páginas públicas (o formulário interno não é medido). *Mitigação:* declarar o limite e comparar com o portal mg.gov.br.

## 7. Ética
- No máximo 1 requisição/s (o script impõe isso) e user-agent identificado. O `robots.txt` da Delegacia Virtual retorna 404, sem restrição publicada.
- **Nenhum boletim é enviado.** Comunicação falsa de crime é crime (CP art. 340). Nenhum formulário é preenchido automaticamente.
- Nenhum dado pessoal é coletado. Os dados da SEJUSP são agregados.
- O portal dados.mg.gov.br bloqueia clientes automatizados (HTTP 403). Respeitamos isso: o download é manual, pelo navegador.

## 8. Plano de coleta
| Fonte | Como | Quando | Arquivo |
|---|---|---|---|
| Lighthouse | `python -m coleta.lighthouse`, 5 rodadas por tela, 4G e 3G, em dias e horários diferentes | semana 1 | `data/lighthouse/resultados.csv` |
| SEJUSP | download manual de dados.mg.gov.br | S01 | `data/sejusp/` |
| PCMG | pedido LAI | protocolar na S01 (prazo 20 + 10 dias) | `data/lai/` |

## 9. Plano de análise
Descritiva (mediana, IQR, boxplots) → testes das H1 a H4 → tamanho do efeito → impacto (M12) → dashboard reaproveitando o do Lab04 (abas Demanda, Território, Qualidade, Impacto).

## 10. Piloto (17/11/2026)
| Página | Disp. | Perf. | Acess. | LCP (s) |
|---|---|---|---|---|
| Delegacia Virtual (início) | mobile | 94 | 77 | 2,4 |
| Delegacia Virtual (início) | desktop | 98 | 77 | 0,5 |
| mg.gov.br: serviço REDS | mobile | 59 | 96 | 7,2 |
| mg.gov.br: serviço REDS | desktop | 92 | 96 | 1,3 |
| mg.gov.br: perda de documento | mobile | 53 | 92 | 6,9 |
| mg.gov.br: perda de documento | desktop | 94 | 93 | 1,2 |

Violações na Delegacia Virtual: `color-contrast`, `html-has-lang`, `image-alt`, `link-name`, `tabindex`. A falta de `lang` e de texto alternativo atrapalha diretamente leitores de tela.

Primeira leitura: a Delegacia Virtual é rápida mas pouco acessível. As páginas do portal que levam o cidadão até ela são acessíveis mas lentas no celular (~7 s). Uma medição só, a confirmar na S02.

## 11. Reaproveitamento dos labs anteriores
- Lab01: coleta automatizada e Kanban no GitHub Projects.
- Lab02: desenho com tratamentos (mobile × desktop; estudo com pessoas).
- Lab03: DORA para a operação (MTBF, MTTR, disponibilidade).
- Lab04: escolha do teste, simulação de poder para definir o nº de repetições, dashboard estilo Power BI.
