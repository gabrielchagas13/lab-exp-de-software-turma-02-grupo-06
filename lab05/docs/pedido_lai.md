# Pedido de acesso à informação (LAI, Lei 12.527/2011) — issue #88

**Responsável:** Marcus Vinicius
**Órgão destinatário:** Polícia Civil de Minas Gerais (PCMG)
**Canal:** e-SIC MG — Sistema Eletrônico do Serviço de Informação ao Cidadão
**Endereço:** <https://acessoainformacao.mg.gov.br/sistema/site/index.aspx>
(confirmado em 17/11/2026; é o canal oficial do Estado de MG, ligado à Ouvidoria-Geral)
**Prazo legal:** 20 dias corridos, prorrogáveis por mais 10 mediante justificativa
(LAI, art. 11, §§ 1º e 2º)

---

## 1. Como protocolar (5 a 10 minutos)

1. Entrar em <https://acessoainformacao.mg.gov.br/sistema/site/index.aspx>.
2. Cadastrar-se ou entrar (pessoa física; é possível usar a conta gov.br).
3. Abrir **novo pedido de acesso à informação**.
4. **Órgão/Entidade destinatário:** *Polícia Civil do Estado de Minas Gerais - PCMG*
   (confirmado: aparece na lista do e-SIC com esse nome exato).
5. **Forma de recebimento da resposta:** *Pelo sistema (com avisos por email)*.
   As outras opções não servem: "buscar/consultar pessoalmente" exige ir ao órgão e
   "correspondência física" tem custo e chega em papel, inútil para um CSV.
6. **Anexos:** nenhum. O pedido não depende de documento, e anexar dados pessoais
   só aumenta o risco à toa.
7. **Identidade preservada:** deixar **desmarcado**. O texto do pedido se identifica
   como pesquisa acadêmica da PUC Minas, então preservar a identidade contradiria o
   próprio corpo do pedido. Marcar ou não **não altera** o prazo nem a obrigação de
   resposta (LAI, art. 11); é só preferência.
8. **Assunto:** `Dados de uso da Delegacia Virtual da PCMG (pesquisa acadêmica)`.
9. Colar o texto da seção 2 abaixo, **trocando apenas a linha de assinatura**.
10. Enviar e **guardar o número de protocolo**.
11. Preencher `docs/protocolo_lai.md` com número, data e prazo, e fechar a issue #88.

> **Não anexe documentos pessoais.** A LAI não exige motivação nem justificativa
> (art. 10, § 3º): dizer que é pesquisa acadêmica é cortesia, não obrigação.

## 2. Texto do pedido (copiar daqui)

Prezados,

Com base na Lei nº 12.527/2011 (Lei de Acesso à Informação), solicito, em **formato
aberto e legível por máquina** (CSV, XLSX ou JSON), nos termos do art. 8º, § 3º,
incisos II e III, as seguintes informações sobre a **Delegacia Virtual da Polícia
Civil de Minas Gerais**, referentes ao período de **2014 até o mês mais recente
disponível**:

1. Quantidade de registros de ocorrência realizados pela Delegacia Virtual, **por mês**.
2. A mesma quantidade **por natureza/tipo de ocorrência** (por exemplo: perda de
   documentos e objetos, furto, estelionato, sinistro de trânsito sem vítima).
3. Se disponível, a quantidade **por município** do fato.
4. Se disponível, a proporção dos registros feitos pela Delegacia Virtual em
   relação ao total de registros de ocorrência (presenciais e online), por mês.
5. Se disponível, os registros de **indisponibilidade do sistema** (datas e
   duração) e a quantidade de registros **iniciados e não concluídos** pelos
   cidadãos.

Não solicito nenhum dado pessoal nem informação protegida: apenas **contagens
agregadas**. Caso algum dos itens esteja sob restrição ou não seja produzido pelo
órgão, peço o **atendimento parcial** dos demais itens, com a indicação expressa de
qual item não pôde ser atendido e por quê, conforme o art. 11, § 1º, inciso II.

Caso a informação já esteja publicada, basta indicar o endereço eletrônico onde ela
pode ser consultada (art. 11, § 6º).

Os dados serão usados exclusivamente para fins acadêmicos, na disciplina de
Laboratório de Experimentação de Software da PUC Minas, e a fonte será citada.

Atenciosamente,

**Marcus Vinicius** — estudante de Engenharia de Software, PUC Minas

## 3. Por que o pedido é assim

| Escolha | Motivo |
|---|---|
| Formato aberto, citando o art. 8º | Reduz a chance de a resposta vir em PDF escaneado, que daria trabalho e perderia precisão |
| Itens numerados de 1 a 5 | Permite atendimento parcial item a item em vez de uma negativa única |
| "Se disponível" nos itens 3 a 5 | Um pedido que exige produção de informação nova pode ser negado (art. 13); assim os itens essenciais (1 e 2) ficam protegidos |
| Pedido explícito de atendimento parcial | Sem isso, um item indisponível costuma travar a resposta inteira |
| Menção ao art. 11, § 6º | Se os dados já existirem publicados, a resposta vem rápida, com o link |

## 4. O que fazer com a resposta

- **Chegando dados:** salvar o arquivo bruto em `data/lai/` com a data no nome,
  registrar o protocolo em `docs/protocolo_lai.md` e avisar o Gabriel — a análise
  (`analise/lai.py`) é tarefa dele na semana 2.
- **Negativa ou silêncio:** cabe **recurso** em 10 dias à autoridade superior
  (art. 15). Registrar a negativa como **limitação** no relatório: o estudo já
  prevê isso e segue com os números de imprensa citados na proposta.
- **Prazo estourado sem resposta:** o estudo não para. A seção de impacto (RQ5) usa
  os números públicos de 2014–2021 e declara a defasagem como ameaça à validade
  externa.

> O pedido é um **complemento** da evidência de impacto, não um bloqueio. Nada no
> Lab05 depende de a resposta chegar dentro do semestre.
