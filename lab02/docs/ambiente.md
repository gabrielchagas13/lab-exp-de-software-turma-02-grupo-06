# Ambiente e Ferramentas do Experimento (Lab02)

Este documento descreve as ferramentas, linguagens e configurações padronizadas que o grupo utilizará durante todos os trials do experimento, para garantir consistência (resolvendo a Issue #30).

## 1. Linguagem de Programação
- **Linguagem Escolhida:** Python 3.10+
- **Justificativa:** Todos os katas do grupo foram elaborados e testados com Python e `pytest`. As ferramentas de métricas estáticas escolhidas (`radon`) funcionam nativamente para Python, o que simplifica o fluxo de coleta de dados.

## 2. Assistente de IA
- **Assistente Escolhido:** GitHub Copilot (via plano gratuito / Student Pack)
- **Justificativa:** É a ferramenta mais integrada às IDEs e amplamente utilizada na indústria, minimizando o overhead de alternar entre o código e o navegador.
- **Configuração no Experimento:**
  - **Tratamento IA:** O assistente deve estar habilitado e ativado. O participante pode usar tanto o autocompletar da linha quanto o chat integrado.
  - **Tratamento Manual:** A extensão do GitHub Copilot (e qualquer outra de IA) **deve** ser desabilitada na IDE antes do início do trial.

## 3. Ambiente de Desenvolvimento (IDE)
- **IDE Padrão:** Visual Studio Code (VS Code)
- **Extensões Necessárias:**
  - Python (Microsoft)
  - GitHub Copilot (desabilitar em trials manuais)
  - Pytest (ou integração nativa de testes do VS Code)

## 4. Cronometragem e Registro de Tempo
- **Método:** Cronômetro integrado ou manual via script do próprio repositório.
- **Uso:** Utilizar o script de cronometragem desenvolvido na Issue #28 (`lab02/scripts/timer.py`) para registrar uniformemente o início e o fim de cada trial, além do tempo total gasto.

## 5. Ferramentas de Métricas Estáticas
O ambiente para o script da Issue #31 dependerá das seguintes ferramentas:
- **Radon:** Coleta de Complexidade Ciclomática (CC) e Linhas de Código (LOC).
- **jscpd:** Ferramenta global (Node.js) para detectar código duplicado. Caso prefira algo 100% Python no script, pode-se usar a métrica nativa do Radon ou pylint, porém o `jscpd` será acionado pelo script principal (`collect_metrics.py`).
