---
id: indice
titulo: Base de conhecimento — CEP-UMC (pré-submissão de protocolos de pesquisa)
tipo: indice
atualizado: 2026-11-25
---

# Base de conhecimento do CEP-UMC

Base em Markdown construída a partir dos **12 documentos oficiais** da pasta `docs/` (modelos do CEP-UMC de fev/2022,
Regimento Interno de 2025, Manual do Pesquisador da Plataforma Brasil e Cartilha de Direitos da CONEP). É a fonte da
**Trilha A** do plugin `cep-umc-tutor` (ver `../README.md`), que ajuda pesquisadores a avaliar seus protocolos **antes**
da submissão ao Comitê de Ética em Pesquisa da Universidade de Mogi das Cruzes. O código do plugin lê as tabelas de
requisitos desta base pelo ID (`skills/cep-tutor/scripts/kb.py`): mantenha o formato `| ID | ... | [SEVERIDADE] |`.

## Estrutura

| Arquivo | Conteúdo | Tipo |
|---|---|---|
| [`00-fontes-e-discrepancias.md`](00-fontes-e-discrepancias.md) | Inventário das fontes, versões, **divergências entre documentos**, limitações | referência |
| [`01-cep-umc-regimento.md`](01-cep-umc-regimento.md) | CEP-UMC: contatos, composição, atribuições, funcionamento | referência |
| [`02-referencias-normativas.md`](02-referencias-normativas.md) | Resoluções e normas citadas e os itens usados | referência |
| [`03-projeto-de-pesquisa.md`](03-projeto-de-pesquisa.md) | Requisitos do projeto detalhado (NO 001/13 e modelo CEP-UMC) | requisitos |
| [`04-tcle.md`](04-tcle.md) | TCLE de adulto em papel: forma e 26 itens de conteúdo | requisitos |
| [`05-tcle-ambiente-virtual.md`](05-tcle-ambiente-virtual.md) | TCLE online (aceite SIM/NÃO, cópia por e-mail) | requisitos |
| [`06-tale-e-tcle-responsavel.md`](06-tale-e-tcle-responsavel.md) | Menores e incapazes: TALE e TCLE do responsável | requisitos |
| [`07-tcle-cessao-amostra-biologica.md`](07-tcle-cessao-amostra-biologica.md) | Cessão de material biológico | requisitos |
| [`08-dispensa-tcle.md`](08-dispensa-tcle.md) | Quando cabe e como pedir a dispensa do TCLE | requisitos |
| [`09-tai-autorizacao-institucional.md`](09-tai-autorizacao-institucional.md) | Termo de Autorização Institucional | requisitos |
| [`10-carta-anuencia-assistencia-gratuita.md`](10-carta-anuencia-assistencia-gratuita.md) | Carta da instituição que dará assistência gratuita | requisitos |
| [`11-plataforma-brasil-submissao.md`](11-plataforma-brasil-submissao.md) | Cadastro, 6 etapas de submissão, documentos obrigatórios | procedimento |
| [`12-tramitacao-pareceres-pendencias.md`](12-tramitacao-pareceres-pendencias.md) | Prazos, tipos de parecer, carta-resposta | procedimento |
| [`13-emendas-notificacoes-recursos.md`](13-emendas-notificacoes-recursos.md) | Pós-aprovação: emendas, relatórios, recursos | procedimento |
| [`14-direitos-dos-participantes.md`](14-direitos-dos-participantes.md) | Os 17 direitos (Cartilha CONEP) mapeados para o TCLE | referência |
| [`15-matriz-documentos-por-tipo-de-estudo.md`](15-matriz-documentos-por-tipo-de-estudo.md) | **Triagem:** 20 perguntas e matriz de documentos por cenário | checklist |
| [`16-checklist-pre-submissao.md`](16-checklist-pre-submissao.md) | **Checklist consolidado** com IDs e severidade | checklist |
| [`17-erros-frequentes-e-sinais-de-alerta.md`](17-erros-frequentes-e-sinais-de-alerta.md) | Padrões textuais de erro → correção | checklist |
| [`18-glossario.md`](18-glossario.md) | Termos e siglas | referência |
| [`19-guia-para-o-tutor.md`](19-guia-para-o-tutor.md) | **Como o plugin deve usar a base**: fluxo, formato dos achados, mapa de recuperação, convenção de IDs | guia |
| [`PLANO-DO-PLUGIN.md`](PLANO-DO-PLUGIN.md) | **Plano do plugin**: Trilha A (ética/CEP) × Trilha B (metodologia, escrita, estatística como sugestões), regra de fronteira, formato do relatório, próximos passos | plano |
| [`fontes/`](fontes/) | **Texto integral** convertido de cada documento original (para citação literal) | texto-integral |

## Escopo
Esta base cobre **apenas as exigências éticas e documentais do CEP** (Trilha A). A avaliação de metodologia, escrita e
estatística (Trilha B) gera **sugestões**, não exigências do CEP, e tem base própria, separada: `../base-academica/`. Ver `PLANO-DO-PLUGIN.md`.

## Convenções

- **Frontmatter YAML** em todos os arquivos: `id`, `titulo`, `tipo`, `aplica_a`, `fontes`, `atualizado`. Ele permite
  filtrar e recuperar arquivos no plugin (RAG por arquivo ou por seção).
- **IDs estáveis** por requisito (ex.: `TCLE-C11`, `PROJ-R06`), para que o tutor cite o requisito exato e para cruzar
  checklist, erros e requisitos. A tabela de prefixos está em `19-guia-para-o-tutor.md`.
- **Severidade** (classificação editorial, não oficial):
  - **[BLOQUEANTE]**: a fonte diz que o problema leva à recusa ou à não aprovação, ou é um documento ou garantia essencial;
  - **[PENDÊNCIA]**: costuma gerar parecer pendente;
  - **[RECOMENDAÇÃO]**: boa prática indicada pelo CEP.
- Cada requisito indica sua **fonte** (documento e item) no frontmatter ou no texto.

## Manutenção
- Quando o CEP-UMC publicar novos modelos, coloque-os em `docs/`, regenere `fontes/` e revise os arquivos curados
  afetados, **mantendo os IDs** existentes.
- Registre as mudanças em `00-fontes-e-discrepancias.md`.
- Depois de editar, rode `uv run skills/cep-tutor/scripts/kb.py stats` e os testes (`uv run --all-extras pytest -q`), que
  conferem se todo ID citado no checklist e nos padrões de erro existe.
