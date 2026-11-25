---
id: dispensa-tcle
titulo: Solicitação de dispensa do TCLE
tipo: requisitos
aplica_a: [estudos retrospectivos com prontuários, laudos ou bases secundárias em que o consentimento é inviável]
documento_plataforma_brasil: "TCLE / Termos de Assentimento / Justificativa de Ausência"
fontes:
  - "Modelo 6 – Dispensa de TCLE – fev/2022 (CEP-UMC) → fontes/modelo-dispensa-tcle.md"
  - "Orientações para elaboração do TCLE – Versão 5 (seção sobre dispensa) → fontes/modelo-tcle.md"
  - "Resolução CNS 466/12, itens IV.8 e III.2.i; Resolução CNS 510/16; Lei 13.709/2018 (LGPD)"
atualizado: 2026-11-25
---

# Dispensa do TCLE

**Base legal (Res. 466/12, IV.8):** "Nos casos em que seja inviável a obtenção do Termo de Consentimento Livre e
Esclarecido ou que esta obtenção signifique riscos substanciais à privacidade e confidencialidade dos dados do
participante ou aos vínculos de confiança entre pesquisador e pesquisado, a dispensa do TCLE deve ser
justificadamente solicitada pelo pesquisador responsável ao Sistema CEP/CONEP, para apreciação, sem prejuízo do
posterior processo de esclarecimento."

## Quando cabe e quando NÃO cabe

| ID | Regra | Severidade |
|---|---|---|
| DISP-01 | Cabe a projetos com **consulta a prontuários** quando **não for possível** colher as assinaturas das pessoas a quem eles se referem. | [BLOQUEANTE] |
| DISP-02 | **NÃO cabe** dispensa quando os prontuários são de instituição onde as pessoas **ainda são atendidas ou participam de atividades** (ali é possível obter o TCLE). | [BLOQUEANTE] |
| DISP-03 | A dispensa é **solicitada por escrito e assinada pelo pesquisador responsável**, e o documento é **anexado à Plataforma Brasil**. A dispensa não é automática: o CEP aprecia o pedido. | [BLOQUEANTE] |
| DISP-04 | Mesmo com a dispensa, aplicar o TCLE **aos participantes que for possível localizar** sem concretizar o risco do item IV.8. | [PENDÊNCIA] |

## Conteúdo obrigatório da solicitação (modelo CEP-UMC)

| ID | Conteúdo | Severidade |
|---|---|---|
| DISP-C01 | Cidade e data; endereçamento "Ao Comitê de Ética em Pesquisa Envolvendo Seres Humanos da Universidade de Mogi das Cruzes". | [PENDÊNCIA] |
| DISP-C02 | Nome completo e CPF do **pesquisador responsável** (quem submeteu na Plataforma Brasil). | [PENDÊNCIA] |
| DISP-C03 | **Título idêntico** ao da Plataforma Brasil. | [PENDÊNCIA] |
| DISP-C04 | **Justificativas específicas do projeto**. Exemplos do modelo: (a) pesquisa **retrospectiva em base de dados secundários**, com acesso a prontuários ou laudos (**especificar**), no local cuja carta de autorização foi apresentada; (b) **impossibilidade de localizar** os indivíduos ou familiares (não frequentam mais o serviço); (c) **mudança de contato** pelo tempo decorrido; (d) **óbito** de muitos pacientes. | [BLOQUEANTE] |
| DISP-C05 | Citação literal do item **IV.8 da Res. 466/12**. | [RECOMENDAÇÃO] |
| DISP-C06 | Compromisso de **confidencialidade, privacidade, proteção da imagem e não estigmatização** (Res. 466/12, III.2.i). | [PENDÊNCIA] |
| DISP-C07 | Compromisso de cumprir as **Res. 466/12 e 510/16 e a LGPD (Lei 13.709/2018)**. | [PENDÊNCIA] |
| DISP-C08 | Compromisso de que a coleta **só começa após a aprovação** do CEP-UMC e de que os dados serão usados **exclusivamente** para a finalidade aprovada. | [PENDÊNCIA] |
| DISP-C09 | Assinatura, nome completo e registro profissional, identidade ou CPF. | [PENDÊNCIA] |

## Documentos que costumam acompanhar
- **TAI** do local onde estão os prontuários ou a base (ver `09-tai-autorizacao-institucional.md`). Ele inclui o
  acesso a documentos na infraestrutura declarada.
- O projeto deve descrever, nos riscos, o **risco de quebra de sigilo** e as medidas de anonimização.

## Sinais de alerta para o tutor
- Pedido de dispensa genérico ("por ser estudo retrospectivo"), sem explicar **por que** o consentimento é inviável.
- Prontuários de pacientes **em acompanhamento ativo** na instituição.
- Ausência do TAI do serviço detentor dos prontuários.
- Texto do modelo não adaptado (ex.: "PRONTUÁRIOS/LAUDOS DE EXAMES – ESPECIFICAR" ainda presente).
