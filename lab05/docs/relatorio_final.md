# Lab05: Relatório final

**A Delegacia Virtual de MG atende bem quem precisa dela?**
Grupo 06: Gabriel Chagas, Marcus Vinicius, Guilherme Lana · PUC Minas · Laboratório de Experimentação de Software

Dashboard: `dashboard/index.html` (`python -m dashboard.gerar`) · Pipeline: `./run_all.sh`

## 1. Introdução
A Delegacia Virtual da Polícia Civil de Minas Gerais (delegaciavirtual.sids.mg.gov.br) está no ar desde 2014 e recebeu mais de 1,5 milhão de boletins online até 2021. Só em 2020 foram cerca de 225 mil registros. Ela atende aos três critérios do laboratório: é **real**, porque é o sistema oficial da PCMG; está **em operação**, porque o registro online vale como o presencial; e tem **alto impacto**, pelo volume de registros e por atender sobretudo perda de documentos, cerca de 68% dos casos.

Avaliamos o sistema por três caminhos combinados: **qualidade do produto** (acessibilidade, desempenho e segurança), **dados de operação** (demanda da SEJUSP e pedido LAI) e **impacto para o cidadão** (custo da espera e público com deficiência visual).

## 2. Perguntas e hipóteses
| RQ | Pergunta | Hipótese | Resultado |
|---|---|---|---|
| RQ1 | É acessível? | H1: toda tela do fluxo tem ≥ 1 violação WCAG A/AA | **Confirmada pelo teste automático** nas 3 telas da DV; teste manual pendente |
| RQ2 | É rápido no celular? | H2: LCP celular > LCP computador | **Confirmada** (p < 0,001, δ de Cliff = 1,0) |
| RQ3 | É seguro? | H3: faltam CSP/HSTS e há bibliotecas JS com CVE | **Confirmada** |
| RQ4 | Que demanda atende? | H4: queda na pandemia e sazonalidade < 10% | **Confirmada** (−32% e ±5%) |
| RQ5 | Quanto custa ao cidadão? | (estimativa, sem teste) | 469 a 2.484 h/ano de espera; ≈ 800 mil mineiros com deficiência visual |

## 3. Método
**Objeto medido:** o fluxo "perda de documento", com 4 telas: a página do serviço no mg.gov.br, o início da Delegacia Virtual, a tela de alerta e a de identificação. Também medimos a página do serviço REDS no mg.gov.br. A tela seguinte à identificação exige CPF, nome e e-mail reais, então a medição para ali. Nenhum formulário é preenchido nem enviado (comunicação falsa de crime é crime, CP art. 340).

**Instrumentos:**
- Lighthouse 13.6.0 em versão fixa, com 5 rodadas por tela em 3 perfis: celular com 4G simulado (RTT 150 ms, 1,6 Mbps, CPU 4×), celular com 3G (RTT 300 ms, 700 kbps) e computador. Ao todo, 75 execuções, sem nenhuma falha (`coleta/validar.py`).
- Coleta passiva de segurança (`coleta/seguranca.py`): cabeçalhos HTTP, versões de TLS aceitas e banners de versão das bibliotecas JS comparados com uma tabela de CVEs públicas.
- Série mensal de furtos da SEJUSP de 2012 a 2026, com download manual porque o portal bloqueia robôs.
- Checklist manual de teclado e VoiceOver: 4 telas × 14 critérios WCAG 2.1 (`data/acessibilidade/checklist.csv`).

**Análise:** mediana e IQR; Wilcoxon pareado unilateral por (tela, rodada); tamanho do efeito pelo r e pelo delta de Cliff; contagem de telas na direção da hipótese; cenários de impacto com análise de sensibilidade.

**Ética:** no máximo 1 requisição/s, user-agent identificado e nenhum dado pessoal coletado.

## 4. Resultados

### RQ1: acessibilidade
- Nota de acessibilidade do Lighthouse: **77 a 80 nas telas da Delegacia Virtual**, contra 92 a 96 nas páginas do mg.gov.br.
- Violações automáticas presentes em todas as telas da DV: `color-contrast`, `html-has-lang` (página sem idioma, então o leitor de tela pode usar a pronúncia errada), `image-alt`, `link-name` e `tabindex`.
- **H1 confirmada pelo teste automático.** O axe-core detecta só uma parte dos problemas; o teste manual com teclado e VoiceOver vai responder à M3 (se dá para concluir a tarefa só com o teclado).

### RQ2: desempenho
| Comparação | Mediana A | Mediana B | Razão | Wilcoxon | δ de Cliff | Telas na direção |
|---|---|---|---|---|---|---|
| Celular 4G × computador | 2,08 s | 0,57 s | 3,6× | p = 6×10⁻⁶ (n = 25) | 1,00 (grande) | 5/5 |
| Celular 3G × celular 4G | 4,28 s | 2,08 s | 2,1× | p = 6×10⁻⁶ | 0,52 (grande) | 5/5 |

- As telas da DV ficam entre 1,8 e 2,1 s no 4G, dentro do limite "bom" de 2,5 s, mas passam de 3,9 s no 3G.
- As páginas do mg.gov.br, por onde o cidadão chega à DV, levam **6,5 a 6,7 s no 4G** e **10 a 14 s no 3G**. Pesam cerca de 2 MB, contra 330 a 400 KB das telas da DV.
- **H2 confirmada.** O gargalo do fluxo não é a Delegacia Virtual, e sim o portal que leva até ela.

### RQ3: segurança
| | Delegacia Virtual | mg.gov.br |
|---|---|---|
| CSP | ❌ | ❌ |
| HSTS | ✅ | ❌ |
| X-Frame-Options / X-Content-Type-Options | ❌ / ❌ | ✅ / ✅ |
| Aceita TLS 1.0/1.1 (obsoletos, RFC 8996) | sim | sim |
| TLS 1.3 | não | não |
| Bibliotecas com CVE | jQuery 1.9.1 e 1.11.1, jQuery UI 1.10.3, Bootstrap 4.0.0 | jQuery 1.9.1 (também carrega 3.7.1) |
| CVEs distintas | 10 | 4 |

As CVEs são de XSS (por exemplo, CVE-2020-11022/11023 no jQuery < 3.5 e CVE-2021-41182 a 41184 no jQuery UI < 1.13). **H3 confirmada.** O resultado mostra exposição, não uma vulnerabilidade explorada: nenhum teste de intrusão foi feito.

### RQ4: demanda
- Furtos consumados em MG caíram de 315 mil (2015) para 207 mil (2025).
- No isolamento (abr–jul/2020), a média mensal ficou **31,9% abaixo** do mesmo período de 2019. A queda é atribuída ao isolamento, não ao sistema.
- Sazonalidade fraca: o maior desvio mensal é de **+5,3%** (março). **H4 confirmada.**
- A região metropolitana de BH responde por 11% a 14% dos furtos da série, com tendência de alta (10,9% em 2012 e 13,7% em 2025).
- Limitação: são crimes registrados por qualquer canal. O número de boletins da DV depende da resposta da LAI (protocolo nº 1510.000360/2026-61, de 17/11/2026; prazo 07/12/2026), ainda não recebida.

### RQ5: impacto
- Espera por registro, somando o LCP das 4 telas do fluxo: **12,3 s no celular 4G**, 26,6 s no 3G e 2,8 s no computador.
- Com ~225 mil registros/ano e 70% deles pelo celular em 4G, o resultado é **≈ 590 horas/ano só esperando as telas aparecerem**. Nos 18 cenários (50–90% no celular, 4G/3G, 4 a 8 telas), a faixa vai de **469 a 2.484 h/ano**. Se todos usassem computador, seriam 172 a 298 h.
- **≈ 800 mil pessoas com deficiência visual em MG.** É uma estimativa: aplicamos à população mineira a taxa nacional do Censo 2022, de 7,9 mi em 203,1 mi (3,9%). Para essas pessoas, as barreiras da RQ1 pesam mais do que o tempo de carregamento.

## 5. Classificação da pesquisa (7 categorias, versão final)
| Categoria | Classificação | Justificativa |
|---|---|---|
| Natureza | Aplicada | Gera recomendações concretas para um serviço público em uso |
| Objetivos | Descritiva e explicativa | Descreve qualidade e demanda e testa hipóteses de diferença (celular × computador, 3G × 4G) |
| Abordagem | Quantitativa, com componente qualitativo | Métricas e testes estatísticos; o checklist manual de acessibilidade é avaliação qualitativa estruturada |
| Procedimentos | Levantamento de campo (medição) + pesquisa documental | Medição do sistema em produção; análise de dados abertos (SEJUSP), imprensa e LAI |
| Tempo | Transversal (sistema) + longitudinal (demanda) | O sistema foi medido em uma janela curta (nov/2026); a demanda, ao longo de 2012–2026 |
| Controle | Quase-experimental | O perfil (celular 4G/3G × computador) foi manipulado e pareado por tela, mas o servidor não foi controlado; a pandemia funciona como série temporal interrompida |
| Nível de evidência | Moderado | Efeitos grandes e consistentes em 5/5 telas, mas sem aleatorização, com poucas telas e com impacto estimado por cenários |

## 6. Recomendações
1. **Acessibilidade (custo baixo):** declarar `lang="pt-BR"`, dar texto alternativo às imagens, dar nome aos links e remover `tabindex` positivo. São correções de uma linha que atingem ≈ 800 mil mineiros com deficiência visual.
2. **Segurança:** atualizar jQuery (≥ 3.5), jQuery UI (≥ 1.13.2) e Bootstrap (≥ 4.3.1); adicionar CSP, X-Frame-Options e X-Content-Type-Options; desativar TLS 1.0/1.1 e ativar TLS 1.3.
3. **Desempenho:** reduzir o peso das páginas do mg.gov.br (~2 MB) que levam à DV, ou linkar direto para a DV nos canais de busca.

## 7. Ameaças à validade e limitações
As ameaças completas, com as mitigações, estão em `docs/proposta_s01.md` §6. As principais:
- **Conclusão:** as 5 rodadas da mesma tela não são independentes. Por isso reportamos também 5/5 telas na direção da hipótese.
- **Interna:** o throttling simulado iguala a rede, mas o servidor pode ter variado. Todas as rodadas foram em 25/11/2026.
- **Construto:** LCP não é igual à experiência completa; a nota do axe é parcial; a segurança foi avaliada só de forma passiva; SEJUSP não é o mesmo que uso da DV.
- **Externa:** só as telas públicas (até a identificação), só MG, uma janela curta e aparelho emulado (moto G Power).
- **Limitações não resolvidas:** o teste manual de acessibilidade e a resposta da LAI estão pendentes; a fração de acessos pelo celular é desconhecida (por isso usamos cenários); a taxa de deficiência visual é nacional, aplicada a MG.

## 8. Conclusão
A Delegacia Virtual **carrega rápido, mas não é acessível nem está atualizada em segurança**. As telas dela ficam perto de 2 s no celular 4G. O caminho até ela, pelo portal mg.gov.br, é o trecho lento, passando de 6 s no 4G e de 10 s no 3G. Todas as telas da DV têm barreiras WCAG que afetam diretamente quem usa leitor de tela, e o sistema carrega bibliotecas JS com 10 CVEs públicas, sem CSP e aceitando TLS 1.0. Pelo volume de uso, cerca de 225 mil registros por ano e cerca de 800 mil potenciais usuários com deficiência visual em MG, essas correções baratas têm alto retorno.

## Fontes
- Tribuna de Minas (30/04/2021): 1,5 mi de boletins e 205,8 mil em jan–nov/2020.
- IBGE, Censo 2022, pessoas com deficiência: [Agência IBGE](https://agenciadenoticias.ibge.gov.br/agencia-noticias/2012-agencia-de-noticias/noticias/43463-censo-2022-brasil-tem-14-4-milhoes-de-pessoas-com-deficiencia), [Agência Brasil](https://agenciabrasil.ebc.com.br/direitos-humanos/noticia/2025-05/brasil-tem-144-milhoes-de-pessoas-com-deficiencia).
- SEJUSP-MG, dados abertos de ocorrências (dados.mg.gov.br).
- Wohlin et al. (2012), *Experimentation in Software Engineering*.
