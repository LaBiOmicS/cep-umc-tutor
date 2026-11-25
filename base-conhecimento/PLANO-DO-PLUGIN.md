---
id: plano-do-plugin
titulo: Plano do plugin tutor — escopo, trilhas de avaliação e próximos passos
tipo: plano
aplica_a: [desenvolvimento do plugin]
atualizado: 2026-11-25
---

# Plano do plugin tutor de pré-submissão

## Objetivo
Ajudar o pesquisador a revisar o protocolo **antes** de submetê-lo ao CEP-UMC. O plugin avalia duas coisas
**diferentes**, que nunca devem se misturar no relatório:

| | **Trilha A — Ética (CEP)** | **Trilha B — Qualidade acadêmica** |
|---|---|---|
| O que avalia | Exigências éticas e documentais do CEP-UMC e das normas que ele aplica | Metodologia, escrita e estatística |
| Natureza | **Requisito**: o CEP pode emitir pendência ou não aprovar | **Sugestão**: melhora o trabalho, mas **não é exigência do CEP** |
| Rótulos | [BLOQUEANTE] / [PENDÊNCIA] / [RECOMENDAÇÃO] | [SUGESTÃO] (sem gradação de severidade ética) |
| IDs | Os desta base (`PROJ-`, `TCLE-`, `TAI-`…) | `SUG-MET-`, `SUG-ESC-`, `SUG-EST-` (a criar) |
| Fonte | `base-conhecimento/` (documentos do CEP-UMC) | Base própria, **separada** (a construir; ver abaixo) |
| Quem decide | O CEP | O pesquisador e o orientador |

**Por que separar:** o CEP avalia questões éticas. Se uma sugestão de estilo ou de estatística aparecer como se fosse
exigência do comitê, o pesquisador pode se preocupar à toa ou atrasar a submissão sem necessidade. E o tutor perde
credibilidade.

## Regra de fronteira entre as trilhas
O próprio modelo de projeto do CEP-UMC define a fronteira (**PROJ-G05**): *o CEP não avalia a metodologia, exceto
quando a metodologia, ou a falta de informação sobre ela, gerar viés ético.*

1. Se o item **está nesta base** (tem ID de requisito), ele é da **Trilha A**. O tutor verifica **presença e coerência**,
   não a qualidade técnica.
2. Se o problema metodológico **gera viés ético**, ele vai para a **Trilha A**, citando PROJ-G05 e explicando o risco
   ético. Exemplos: amostra maior que o necessário expõe pessoas a risco sem motivo; desenho incapaz de responder à
   pergunta expõe participantes sem benefício de conhecimento; grupo-controle sem acesso à intervenção eficaz.
3. Todo o resto (qualidade técnica, redação, escolha de testes, poder estatístico, clareza) é **Trilha B**.

O mesmo tema pode render um achado em cada trilha:

| Tema | Trilha A (CEP) | Trilha B (sugestão) |
|---|---|---|
| Tamanho da amostra | PROJ-M02: informa **quantos** e **como chegou** a esse número? | O cálculo é adequado (poder, efeito, α)? |
| Plano de análise | PROJ-C07: o plano de análise **existe**? | Os testes escolhidos são apropriados aos dados? |
| Critérios de elegibilidade | PROJ-M05: exclusão não é a antítese da inclusão | Os critérios limitam a validade externa? |
| Riscos | PROJ-R*: riscos descritos, com medidas de minimização | — |
| Redação | TCLE-C*: linguagem acessível ao participante (exigência) | Coesão, concisão e normas de citação do projeto |
| Objetivos | PROJ-N/C: objetivos presentes e iguais em todos os documentos | Objetivos mensuráveis e alinhados ao desenho |

## Formato do relatório
O relatório tem **duas partes, sempre nesta ordem e com títulos explícitos**:

1. **Parte 1 — Pontos éticos e documentais (avaliados pelo CEP)**: ordenados por severidade, no formato descrito em
   `19-guia-para-o-tutor.md`.
2. **Parte 2 — Sugestões acadêmicas (não são exigências do CEP)**: metodologia, escrita e estatística. A parte começa com
   o aviso: *"Os itens abaixo não serão cobrados pelo CEP. São sugestões para melhorar o trabalho; decida com seu
   orientador."*

Regras de redação da Parte 2:
- Nunca usar "o CEP exige", "pode gerar pendência" ou rótulos de severidade ética.
- Usar "sugerimos", "considere", "pode fortalecer".
- Se a Parte 1 tiver itens [BLOQUEANTE], lembrar que eles têm prioridade sobre as sugestões.
- O pesquisador pode pedir **só a Trilha A** (revisão rápida para submeter) ou **só a Trilha B**.

## Trilha B em um CEP universitário: calibrar pelo nível do trabalho
A referência da Trilha B são **as melhores práticas científicas**, em todos os níveis. Mas o CEP-UMC recebe trabalhos de
alunos de graduação (IC, TCC), especialização e residência, mestrado e doutorado, além de pesquisas de docentes. O
**nível** não muda o que é correto. Muda **o que se espera**, **o que priorizar** e **como dizer**.

O tutor pergunta o nível na triagem (Q21 em `15-matriz-documentos-por-tipo-de-estudo.md`) ou o infere da folha de rosto
e do projeto. Se não for possível saber, trata o trabalho como de **graduação**, o nível mais didático.

### O que avaliar: núcleo comum e expectativa por nível
**Núcleo comum (todos os níveis).** Erro é erro em qualquer nível, e estes itens são sempre apontados:
- coerência entre pergunta, objetivos, desenho, variáveis e plano de análise;
- análise incompatível com o tipo de dado ou com o desenho (ex.: teste para amostras independentes em dados pareados);
- tamanho de amostra sem nenhuma justificativa;
- conclusões ou resultados esperados que o desenho não sustenta (ex.: causalidade em estudo transversal);
- instrumentos de coleta sem origem ou validação informada;
- referências ausentes, inconsistentes ou plágio aparente.

**Expectativa crescente.** Itens de aprofundamento são cobrados conforme o nível:

| Tema | Graduação (IC/TCC) | Especialização / residência | Mestrado | Doutorado / docente |
|---|---|---|---|---|
| Tamanho da amostra | Justificativa clara. Amostra de conveniência é aceitável se declarada como **limitação** | Justificativa. Cálculo formal se o objetivo for inferencial | **Cálculo formal** esperado em estudos inferenciais (efeito, α, poder, perdas) | Cálculo formal, com fonte do tamanho de efeito e análise de sensibilidade quando couber |
| Plano de análise | Descritivo correto e teste principal adequado | Testes adequados e pressupostos citados | Pressupostos, ajuste para confundidores, tratamento de dados faltantes | Tudo isso, mais modelagem justificada, comparações múltiplas e pré-especificação |
| Diretrizes de relato (EQUATOR) | Apresentar a diretriz como **material de estudo** | Recomendar | Esperado seguir | Esperado seguir e citar |
| Viés e validade | Reconhecer as principais limitações | Identificar vieses principais | Estratégias para controlar vieses | Discussão completa de validade interna e externa |
| Escrita | Estrutura, clareza, ortografia, normas de citação | Clareza e concisão | Argumentação, lacuna da literatura, literatura atual | Contribuição original explícita e posicionamento no campo |

### Como reportar: tom e formato por nível
- **Separar em dois blocos**:
  - **"Essencial"**: núcleo comum e o que se espera para o nível;
  - **"Para aprofundar"**: opcional, acima do nível.
  Em graduação, limitar o bloco "Essencial" a **até 5 itens**, em ordem de impacto, e deixar o resto em "Para
  aprofundar", para não sobrecarregar o aluno.
- **Começar pelos pontos fortes** do trabalho (de 1 a 3), sobretudo para alunos.
- **Graduação e especialização (tom formativo):**
  - explicar o conceito em linguagem simples, com um exemplo;
  - indicar uma leitura ou recurso para estudar;
  - formular parte das sugestões como **perguntas de reflexão** (ex.: "O que você espera encontrar e quantas pessoas
    seriam necessárias para detectar essa diferença?");
  - não reescrever o texto do aluno.
- **Mestrado e doutorado:** tom técnico, explicação breve, referência metodológica específica.
- **Docente:** direto e conciso, só o apontamento técnico e a referência.
- **Papel do orientador:** em trabalho de aluno, o orientador é o pesquisador responsável e as escolhas metodológicas
  costumam ser dele ou combinadas com ele. O tutor:
  - não desautoriza essas escolhas: apresenta alternativas e recomenda **conversar com o orientador**;
  - acrescenta ao fim da Parte 2 um **resumo para o orientador**, com 3 a 5 linhas sobre os pontos essenciais.
- **Nunca** condicionar a submissão ao CEP às sugestões da Trilha B.

Formato sugerido de achado da Trilha B (graduação):

```
[SUGESTÃO · Essencial] SUG-EST-03 — Tamanho da amostra sem justificativa
Onde: Projeto, Metodologia, "Serão entrevistados 30 alunos."
Por que importa: sem justificar o número, não dá para saber se o estudo consegue responder à pergunta.
Para refletir: por que 30? Seu objetivo é descrever o grupo ou comparar grupos?
Como melhorar: se for descritivo, justifique a escolha (ex.: todos os alunos da turma) e cite a limitação; se for
comparar, converse com seu orientador sobre um cálculo amostral.
Para estudar: <referência da base-academica>
```

## Base de conhecimento da Trilha B (versão inicial em `../base-academica/`)
- Pasta **separada**, para que `base-conhecimento/` continue contendo apenas o que vem do CEP-UMC.
- Mesmas convenções desta base: frontmatter YAML, IDs estáveis (`SUG-MET-`, `SUG-EST-`, `SUG-ESC-`), fonte de cada item.
- Cada item traz **núcleo comum** (sim/não), **nível mínimo** (a partir do qual é "Essencial"), por que importa e onde
  estudar.
- Arquivos:
  - `01-metodologia.md`, `02-estatistica.md` e `03-escrita.md`: 42 itens;
  - `04-diretrizes-de-relato.md`: diretriz EQUATOR por desenho;
  - `05-expectativas-por-nivel.md`: o que se espera e o tom em cada nível.
- Fontes usadas na versão inicial:
  - diretrizes da rede EQUATOR (CONSORT, SPIRIT, STROBE, STARD, COREQ, SRQR, CROSS, CHERRIES, CARE, PRISMA, SAMPL,
    SAGER);
  - normas ABNT (NBR 15287, 14724, 6023, 10520);
  - literatura metodológica clássica.
- **Falta acrescentar** o material interno da UMC (manuais de TCC, regulamentos dos programas de pós) e validar a base
  com coordenadores.

## Implementação (plugin `cep-umc-tutor`, v0.2.0)
- **Skill:** `skills/cep-tutor/`, com quatro modos: planejamento (sem documentos), revisão completa, consulta à base e
  carta-resposta.
- **Subagente:** `agents/cep-reviewer.md`, um por trilha.
- **Etapas determinísticas** (`cep_tutor.py`):
  - `prepare`: extração, tipo de documento, triagem, nível, esperados × recebidos e sinais automáticos;
  - `compile`: severidade tirada desta base, Essencial × Para aprofundar por regra, relatório em duas partes.
- As duas trilhas recebem prompts separados: a Trilha A recebe só esta base e os documentos; a Trilha B recebe só a base
  acadêmica, o projeto e os instrumentos, com a lista do que pertence à Trilha A.
- **A avaliação é finita:**
  - até 3 rodadas por protocolo;
  - da 2ª rodada em diante, só verificação: itens novos apenas se forem bloqueantes ou pendências na Trilha A, ou do
    núcleo comum na Trilha B;
  - depois da 3ª, só a Trilha A, em verificação;
  - 2 tentativas por tarefa;
  - teto de itens por bloco.

  Motivo: evitar o ciclo "corrige, aparece mais coisa", que desgasta o aluno e atrasa a submissão sem ganho ético.
- **Saídas por perfil:**
  - `planejamento.md`, para quem está começando;
  - `relatorio.md`, para o autor;
  - `relatorio_orientador.md`, uma página para o orientador.

## Próximos passos
1. Validar `base-academica/`, sobretudo a tabela de expectativas por nível, com coordenadores de curso e de pós, e
   acrescentar o material interno da UMC.
2. Testar com protocolos reais, já avaliados pelo CEP, para calibrar a severidade da Trilha A, os sinais automáticos e
   a utilidade da Trilha B.
3. Validar com o CEP-UMC os pontos de `00-fontes-e-discrepancias.md` (horário de atendimento, classificação de
   severidade).
4. Futuro (não implementado):
   - modo em lote para orientadores com vários alunos (hoje é uma pasta de saída por aluno);
   - conferência do cálculo amostral;
   - versão para quem não usa a CLI (Projeto no claude.ai com as duas bases).
