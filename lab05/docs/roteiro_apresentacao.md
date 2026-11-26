# Roteiro da apresentação (10 min)

Apresentar com o dashboard aberto (`dashboard/index.html`), rolando seção por seção. Quem fechou a issue apresenta o bloco.

| Tempo | Bloco | Quem | O que mostrar / falar |
|---|---|---|---|
| 0:00–1:00 | Abertura | Gabriel | Pergunta central. Por que a DV: real, em operação, alto impacto (1,5 mi de boletins, 225 mil/ano, 68% perda de documento). Seção 01 |
| 1:00–2:00 | Perguntas e método | Gabriel | Tabela RQ1–RQ5 (seção 02). Fluxo "perda de documento" com 4 telas, parada antes dos dados pessoais (ética, CP art. 340). 7 categorias em uma frase |
| 2:00–3:30 | Coleta | Marcus | Lighthouse 13.6 fixo, 5 rodadas × 3 perfis × 5 telas = 75 execuções, 0 falhas. Coleta de segurança passiva, 1 req/s. `run_all.sh` |
| 3:30–5:00 | RQ2 desempenho | Guilherme | Boxplot da seção 03. Celular 4G 3,6× mais lento, p < 0,001, δ = 1,0, 5/5 telas. **Recado:** a DV é rápida; o portal mg.gov.br é que pesa 2 MB e leva 6–14 s |
| 5:00–6:00 | RQ1 acessibilidade | Gabriel | Nota 77–80 na DV contra 92–96 no portal. As 5 violações e o que significam para quem usa leitor de tela. Resultado do teste com VoiceOver (se feito, mostrar um trecho de vídeo) |
| 6:00–7:00 | RQ3 segurança | Marcus | Tabela da seção 04: jQuery 1.9/1.11, jQuery UI 1.10, Bootstrap 4.0, 10 CVEs, sem CSP, aceita TLS 1.0. Deixar claro: exposição, não ataque |
| 7:00–8:00 | RQ4 demanda | Gabriel | Série SEJUSP: −32% no isolamento, sazonalidade ±5%. LAI protocolada em 17/11 (nº 1510.000360/2026-61), prazo 07/12 |
| 8:00–9:00 | RQ5 impacto | Guilherme | Calculadora ao vivo: mudar o % no celular e a rede. 469–2.484 h/ano. ≈ 800 mil com deficiência visual em MG |
| 9:00–10:00 | Conclusão | Todos | 3 recomendações baratas (lang/alt, atualizar bibliotecas + CSP, aliviar o portal). Principais ameaças: 5 telas, segurança passiva, % no celular desconhecido |

## Perguntas prováveis
- **Por que não mediram o formulário inteiro?** Exige CPF e e-mail reais, e enviar seria comunicação falsa de crime. Declarado como limitação externa.
- **n = 25 com rodadas repetidas não infla o p-valor?** Sim, por isso reportamos também 5/5 telas na direção e o δ de Cliff.
- **De onde vem o 800 mil?** Taxa nacional do Censo 2022 (3,9%) aplicada à população de MG. É estimativa.
- **As CVEs são exploráveis ali?** Não testamos (ética). Elas indicam bibliotecas desatualizadas com falhas públicas de XSS.
