# Mapa do fluxo "perda de documentos e objetos" (issue #90)

**Objetivo:** identificar todas as telas que o cidadão atravessa para registrar uma
ocorrência de perda de documentos na Delegacia Virtual de MG, **até a revisão, sem
enviar**, e marcar quais delas podem ser medidas de fora (RQ1, acessibilidade; RQ2,
desempenho).

**Mapeado em:** 17/11/2026 · **Responsável:** Marcus Vinicius ·
**Artefatos:** `coleta/mapa_fluxo.py`, `data/fluxo/telas.csv`, `config.json`

> **Nenhum boletim foi enviado e nenhum formulário foi preenchido.** O mapeamento
> faz apenas requisições GET, com no mínimo 1 s entre elas, como um cidadão que
> navega e desiste. A proibição está no código: `SessaoSomenteLeitura` recusa
> POST, PUT, DELETE e PATCH, e um teste automatizado verifica isso.

## 1. O fluxo tem 5 etapas; 3 são medíveis de fora

| # | Tela | URL | Medível | Como se avança |
|---|---|---|---|---|
| 1 | Escolha da natureza | `/sxgn/` | ✅ | link **GET** para a natureza escolhida |
| 2 | Alerta e termo de ciência | `/sxgn/ocorrencia/renderAlerta?tipoNatureza=2` | ✅ | link **GET** "Estou ciente. Continuar" |
| 3 | Identificação inicial | `/sxgn/ocorrenciaPerdaDocumentosObjetos/renderIdentificacao` | ✅ | **POST** + captcha |
| 4 | Dados da ocorrência (local, data, objetos) | — | ❌ | **POST** |
| 5 | Revisão antes do envio | — | ❌ | **POST** (o estudo para aqui) |

"Perda de documentos e objetos" é a **natureza 2** das 13 oferecidas. É a mais
relevante para o estudo: segundo a PCMG, respondeu por cerca de **68%** de todos os
registros da Delegacia Virtual.

### Por que as telas 4 e 5 não são medíveis automaticamente

A partir da identificação, o wizard não tem mais uma URL por tela: todas as etapas
seguintes são renderizadas pelo mesmo endereço,
`POST /sxgn/ocorrenciaPerdaDocumentosObjetos/index`, e o avanço depende de enviar
**nome, CPF, RG, data de nascimento, celular e e-mail** mais um **captcha**.

Chegar nelas por script exigiria preencher dados pessoais e derrotar o captcha —
as duas coisas estão fora do combinado (seção 7 da proposta) e a segunda é abuso
do serviço. Então o mapa delas é **manual**, pela seção 3 deste documento.

## 2. O que foi medido nas três telas acessíveis

Dados de `data/fluxo/telas.csv` (17/11/2026):

| # | Tela | HTTP | Tamanho | Campos | Captcha | Relógio de sessão |
|---|---|---|---|---|---|---|
| 1 | Escolha da natureza | 200 | 37 KB | 0 | não | não |
| 2 | Alerta e termo de ciência | 200 | 12 KB | 0 | não | não |
| 3 | Identificação inicial | 200 | 45 KB | **17** | **sim** | **sim** |

Três achados que valem para a análise:

- **A tela 3 concentra tudo.** É a mais pesada do trecho público, tem 17 campos
  obrigatórios, captcha e um relógio de expiração de sessão. Se há um gargalo de
  acessibilidade ou de desempenho no fluxo, é mais provável que esteja aqui.
- **O relógio de sessão é um risco de usabilidade** que nenhuma nota automática
  captura: o cidadão preenche sob pressão de tempo e, se a sessão cair, recomeça.
  Entra como observação qualitativa na RQ1 e no impacto (RQ5).
- **O captcha é imagem** (`/sxgn/captcha/renderizarImagemCaptcha`). Captcha visual
  sem alternativa acessível é falha de WCAG 1.1.1; confirmar no teste manual com
  leitor de tela, porque o Lighthouse sozinho não decide isso.

## 3. Protocolo do mapeamento manual (telas 4 e 5)

Feito por uma pessoa, no navegador, **uma vez**, com dados fictícios e **sem clicar
em enviar**. Leva cerca de 15 minutos.

> ⚠️ **Regra que não se negocia:** não existe clique em "Enviar"/"Finalizar".
> Comunicação falsa de crime é crime (CP art. 340). Ao chegar na tela de revisão,
> registre o que precisa e **feche a aba**.

1. Abrir `https://www.delegaciavirtual.sids.mg.gov.br/sxgn/` em janela anônima.
2. Escolher **Perda de documentos e objetos** → **Estou ciente. Continuar**.
3. Na identificação, preencher com **dados fictícios** (não use CPF real, seu ou de
   terceiros) e resolver o captcha manualmente.
4. Para **cada** tela nova que aparecer, registrar em
   `data/fluxo/telas_manuais.csv`:
   - `etapa`, `nome` da tela (o título visível)
   - `campos_obrigatorios` (quantos têm asterisco)
   - `tipos_de_campo` (texto, data, seleção, upload…)
   - `exige_upload` (sim/não) e `exige_documento_extra`
   - `erros_de_validacao` que apareceram, se apareceram
   - `screenshot` (nome do arquivo em `docs/img/fluxo/`)
5. Na **tela de revisão**, conferir que ela mostra o resumo antes do envio,
   registrar e **fechar a aba sem enviar**.
6. Rodar `python -m coleta.mapa_fluxo` para atualizar a parte automática e
   conferir que as três primeiras telas continuam respondendo 200.

Se alguma tela nova tiver URL própria (o que não esperamos), acrescente-a a
`config.json` em `paginas` **e** em `fluxo_perda_documento.telas` com
`"mapeavel": true` — o teste `test_telas_mapeaveis_entram_nas_paginas_medidas`
cobra essa consistência.

## 4. O que isso muda nas RQs

| Onde | Consequência |
|---|---|
| **RQ1 / H1** | A verificação de WCAG cobre 3 das 5 telas por ferramenta automática. As telas 4 e 5 entram pelo checklist manual (teclado + leitor de tela). Se houver violação de nível A/AA nas três medidas, H1 já se sustenta para o trecho público. |
| **RQ2 / H2** | O Wilcoxon pareado celular × computador roda sobre **3 telas × repetições**, não 5. Pareamento por tela continua válido; o n é que é menor. |
| **RQ5** | A conta de horas de espera usa o LCP das telas medidas. Como a tela 3 é a mais pesada e as não medidas são formulários parecidos, a estimativa com 3 telas **subestima** o custo total. Declarar isso na sensibilidade. |
| **Validade externa** | Já estava na proposta ("o formulário interno não é medido"); agora está quantificado: 3 de 5 telas, e justamente as 2 ausentes são as de maior esforço de preenchimento. |

## 5. Como reproduzir

```bash
cd lab05
python -m coleta.mapa_fluxo          # 3 GETs, 1 s entre eles -> data/fluxo/telas.csv
python -m pytest tests/test_mapa_fluxo.py -q
```

O mapeamento é seguro de repetir: três requisições GET, o mesmo que abrir três
páginas no navegador.
