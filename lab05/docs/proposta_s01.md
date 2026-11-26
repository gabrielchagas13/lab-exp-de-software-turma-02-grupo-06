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

## 6. Ameaças à validade (versão S02)
Classificação de Wohlin et al. (2012). Cada ameaça tem a mitigação adotada e o que fica como limitação.

### 6.1 Validade de conclusão
- **Variabilidade do Lighthouse:** a nota e o LCP mudam entre execuções (rede, carga do servidor). *Mitigação:* 5 repetições por tela e perfil, mediana e IQR em vez de média, testes não paramétricos (Wilcoxon pareado) e tamanho do efeito (r, delta de Cliff), não só o p-valor.
- **Pares não independentes:** as 5 repetições da mesma tela são correlacionadas, então o n = 25 do Wilcoxon superestima a informação. *Mitigação:* também reportamos em quantas das 5 telas a mediana segue a direção da hipótese.
- **Baixo poder:** só 4–5 telas. *Limitação:* o resultado vale como evidência descritiva forte, não como generalização estatística para todo o sistema.

### 6.2 Validade interna
- **Rede e máquina do grupo:** influenciam o tempo. *Mitigação:* throttling *simulado* do Lighthouse (o mesmo perfil 4G/3G para todas as telas), mesma máquina, horário registrado em cada linha.
- **Mudança do sistema durante a coleta:** um deploy no meio da coleta mudaria o objeto medido. *Mitigação:* a coleta de cada rodada é feita em uma sessão curta; scripts e bibliotecas detectados ficam salvos (`data/seguranca/bibliotecas.csv`) para comparar.
- **Cache/CDN:** a primeira carga pode ser mais lenta. *Mitigação:* o Lighthouse sempre inicia com cache limpo, e todas as telas recebem o mesmo tratamento.

### 6.3 Validade de construto
- **Nota automática ≠ experiência real:** o axe-core detecta só uma parte dos problemas WCAG, e um site pode "jogar" a nota (Goodhart). *Mitigação:* olhamos as violações concretas e fazemos o teste manual com teclado e VoiceOver (`data/acessibilidade/checklist.csv`).
- **LCP como proxy de "espera":** o LCP mede quando o maior elemento aparece, não quando o cidadão consegue agir. *Mitigação:* reportamos também TBT e Speed Index; na RQ5 o custo é tratado como estimativa com análise de sensibilidade.
- **Segurança só passiva:** cabeçalhos, TLS e versões de bibliotecas mostram *exposição*, não uma vulnerabilidade explorável. Não fazemos testes de intrusão (ética). As CVEs vêm de uma tabela de versões conhecidas, e a detecção depende do banner da biblioteca no arquivo minificado (falsos negativos possíveis).
- **SEJUSP como demanda:** são crimes registrados por qualquer canal, não boletins da Delegacia Virtual. *Mitigação:* tratados como demanda potencial; o número real de uso depende da resposta da LAI.

### 6.4 Validade externa
- **Só as telas públicas:** o fluxo é medido até a identificação; as telas seguintes exigem dados pessoais reais e não são acessadas (ética, CP art. 340). O resultado não cobre o formulário interno.
- **Só MG e uma janela curta de tempo:** não generaliza para outros estados nem para o sistema ao longo dos anos. *Mitigação:* comparação com as páginas do portal mg.gov.br que levam o cidadão até a Delegacia Virtual.
- **Aparelho simulado:** o perfil "mobile" do Lighthouse é um Moto G Power emulado; aparelhos mais baratos seriam mais lentos (o resultado é conservador).

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

**Por que 5 rodadas por tela e dispositivo.** Simulação de poder em `analise/poder.py` (reaproveita a ideia do Lab04: repetir o experimento 1.000 vezes com a verdade conhecida e contar as rejeições). Modelo em escala log: diferença celular − computador = efeito + variação entre telas + ruído de rodada; teste: Wilcoxon pareado unilateral (H2), α = 0,05, poder-alvo 80%. Do piloto de 17/11 saem o efeito (razão celular/computador de 5,6×, o que é enorme) e a variação entre telas (σ = 0,05 em log). A variância **entre rodadas não saiu do piloto**: cada tela foi medida uma vez por dispositivo. Por isso ela entra como grade (σ_rodada de 0,05 a 0,30), e a primeira rodada da S02 deve substituí-la pelo valor medido.

Rodadas mínimas para poder ≥ 80% (teste sobre as rodadas pareadas; tabela completa em `data/poder/poder_rodadas.csv`):

| Telas | Efeito | σ_rodada 0,05 | 0,10 | 0,20 | 0,30 |
|---|---|---|---|---|---|
| 5 | 1,25× | 1 | 2 | 3 | 5 |
| 5 | 1,5× | 1 | 1 | 2 | 2 |
| 5 | piloto (5,6×) | 1 | 1 | 1 | 1 |
| 3 | 1,25× | 2 | 2 | 5 | 10 |
| 3 | 1,5× | 2 | 2 | 2 | 5 |
| 3 | piloto (5,6×) | 2 | 2 | 2 | 2 |

Decisão: **manter 5 rodadas.** Com as 5 telas do fluxo, 5 rodadas dão poder ≥ 80% até para um efeito de 1,25× com a pior variância da grade. Com apenas as 3 telas medíveis (`docs/fluxo_perda_documento.md`), 5 rodadas cobrem efeitos de 1,5× ou mais; para detectar 1,25× com σ_rodada = 0,30 seriam 10. Regra de revisão: se a σ_rodada medida na S02 passar de 0,20 e só houver 3 telas, subir para 10 rodadas.

Duas ressalvas, ambas viram ameaça à validade (§6):
1. Tratar cada rodada como um par independente é pseudo-replicação: rodadas da mesma tela não são independentes. Por isso o teste por tela (mediana das rodadas, k pares) é reportado ao lado. Com k = 3 o menor p-valor unilateral possível é 0,125, então **esse teste nunca rejeita a 5%**; com k = 5 é 0,031 e só rejeita se as 5 telas forem no mesmo sentido.
2. O efeito do piloto (5,6×) é tão grande que 1 ou 2 rodadas bastariam para H2. As 5 rodadas existem para estimar a variância, para as notas (M1, M6) e para o horário, não só para H2.

## 9. Plano de análise
Ordem: descritiva (mediana, IQR, boxplots) → testes das H1 a H4 → tamanho do efeito → impacto (M13) → dashboard reaproveitando o do Lab04 (abas Demanda, Território, Qualidade, Impacto).

**Regras gerais.** α = 0,05 por hipótese, bilateral salvo onde a hipótese tem direção (H2, H4-queda). Como são 4 hipóteses, o p-valor reportado também vem com a correção de Holm (família de 4); a conclusão só muda se as duas leituras discordarem, e aí as duas aparecem. Testes não paramétricos, porque LCP e peso são assimétricos e a nota do Lighthouse é ordinal (nota da §3). Todo teste vem com tamanho do efeito e intervalo de confiança, nunca só com o p-valor (lição do Lab04).

| Hip. | Métrica e escala | Teste | α | Tamanho do efeito | Efeito mínimo de interesse |
|---|---|---|---|---|---|
| H1 | M2 nº de violações A/AA por tela (razão); M1 nota de acessibilidade (ordinal); M3 conclui só com teclado (nominal) | Binomial exato unilateral sobre a proporção de telas com ≥ 1 violação A/AA (H0: ≤ 50%). M1 e M3 só descritivas | 0,05 | Proporção de telas com violação e IC de Clopper-Pearson. Com 5 telas e 5 violando: p = 0,031 | Proporção > 50% |
| H2 | M4 LCP em ms (razão); M5 peso em KB (razão); M6 nota de performance (ordinal) | Wilcoxon de postos sinalizados pareado, unilateral (celular > computador). Par = mesma tela e mesma rodada. Confirmação por tela (mediana das rodadas) | 0,05 | r = Z/√N; delta de Cliff; razão de medianas de Hodges-Lehmann (em log) com IC | Razão ≥ 1,25× no LCP (a simulação da §8 usa esse valor) |
| H3 | M7 nota SSL Labs (ordinal); M8 cabeçalhos ausentes (razão); M9 bibliotecas com CVE (razão) | Sem teste inferencial: o sistema é medido inteiro, não é amostra. Reporta presença/ausência de CSP e HSTS e contagens, com a versão e a data da medição | não se aplica | Contagem e lista | CSP ou HSTS ausente, ou ≥ 1 biblioteca com CVE |
| H4 | M11 ocorrências/mês (razão); M12 desvio sazonal em % (razão) | Queda: série interrompida (OLS com dummies de mês e erros robustos HAC) para abr–jul/2020. Sazonalidade: Kruskal-Wallis do mês do ano (teste) e amplitude do índice sazonal comparada a 10% | 0,05 | Queda em % contra o contrafactual da tendência, com IC; amplitude sazonal em pontos percentuais | Queda ≥ 10% e amplitude sazonal < 10% |

Observações:
- **Escalas.** Notas do Lighthouse e SSL Labs são ordinais: mediana e IQR, nunca média. LCP, peso, contagens e ocorrências são razão: podem usar razão entre medianas.
- **H1** é quase uma verificação, não um teste estatístico clássico: o resultado vem das violações concretas (axe/Lighthouse). A binomial só dá o nível de confiança de generalizar de 5 telas para o fluxo.
- **H2** usa as 5 rodadas por tela definidas pelo poder (§8). O teste por rodada tem poder, mas supõe rodadas independentes; o teste por tela é o conservador e, com 3 telas, não consegue rejeitar (p mínimo 0,125). Se só as 3 telas forem medíveis, a conclusão de H2 se apoia no teste por rodada e no tamanho do efeito, e isso é declarado como limitação.
- **H4** trata o isolamento (abr–jul/2020) como intervenção: é quase-experimento, sem grupo de controle, e a queda pode misturar pandemia com outras causas.

**Impacto (M13).** Horas de espera/ano = registros/ano (M10) × nº de telas do fluxo × LCP mediano (M4). Entra como análise de sensibilidade: o LCP varia entre o celular e o computador, e os registros entre a imprensa e a resposta da LAI, então o resultado é uma faixa, e não um número só. M14 (população com deficiência visual em MG, IBGE) vem de fonte externa e só entra como contexto.

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
