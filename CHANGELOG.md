# Changelog

Todas as mudanças relevantes deste plugin. O formato segue o [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/)
e as versões seguem o [SemVer](https://semver.org/lang/pt-BR/).

## [0.2.0] — 2026-11-25

Revisão sob o olhar de três perfis: aluno de graduação, aluno de pós e orientador.

### Adicionado
- **Avaliação finita:**
  - até 3 rodadas por protocolo (`--max-rodadas`), contadas por versão dos documentos (`historico/`);
  - da 2ª rodada em diante, os revisores só verificam os itens anteriores. Itens novos entram apenas se forem
    bloqueantes ou pendências (Trilha A) ou do núcleo comum (Trilha B), e o código descarta o resto;
  - depois do limite, o ciclo se encerra: só a Trilha A roda, em verificação;
  - 2 tentativas por tarefa: depois disso, `next` marca a tarefa como `falhou`;
  - tetos por bloco:
    - Essencial: 5, 6 ou 8 conforme o nível;
    - Para aprofundar: 5;
    - recomendações: 8;
    - pontos para conferir: 10.
- **Progresso entre rodadas:** itens resolvidos, ainda pendentes e novos, comparados por ID e documento.
- **Relatório do orientador** (`relatorio_orientador.md` / `.pdf`): situação, plano de ação, assinaturas (PB-D01,
  TCLE-F10, TAI-09, ANU-10), prazo e sugestões essenciais.
- **Relatório do aluno:**
  - "Comece por aqui" (até 5 ações: documentos faltantes, bloqueantes, pendências);
  - legenda dos rótulos;
  - prazo de submissão calculado a partir do início da coleta no cronograma, com alerta quando a data já passou;
  - "quem submete" na graduação (PB-U03);
  - link dos modelos.
- **`planejar`:** modo sem documentos, que gera `planejamento.md` com documentos, assinaturas, prazo e erros comuns
  (Modo 0 da skill).
- Novo tipo de documento: "Informações Básicas do Projeto" (PDF da Plataforma Brasil). A Trilha A compara esse PDF
  com o projeto (PB-S06/S07).
- Alerta quando um documento é truncado.
- Página do GitHub Pages (`site/`, workflow `pages.yml`), no mesmo modelo dos outros plugins LaBiOmicS:
  - em PT, EN e ES;
  - guia passo a passo por sistema operacional e por IA (Claude Code ou Antigravity);
  - terminal e fluxo animados;
  - prompts prontos, perfis, limites de rodadas, saídas e perguntas frequentes.

  Logo em `assets/`.
- README em português (`README.md`, língua principal), com versões em inglês (`README.en.md`) e espanhol (`README.es.md`).
  A página também abre em português; inglês e espanhol ficam no seletor.

### Alterado
- Limite de texto por documento: de 60 mil para 250 mil caracteres (projetos de dissertação e tese).
- O problema vem antes do ID no título de cada achado.
- "Sinais automáticos não verificados" passou a se chamar "Pontos para conferir".
- `plugin.json` (Antigravity): 3 prompts sugeridos, para passar no `agy plugin validate --strict` usado pelo `install.sh`.
- A skill orienta a apresentação conforme quem pede: aluno de graduação, aluno de pós ou orientador.

## [0.1.0] — 2026-11-25

### Adicionado
- Primeira versão do tutor de pré-submissão ao CEP-UMC.
- **Duas trilhas separadas:**
  - **Trilha A** (ética e documentos): IDs e severidade da base do CEP-UMC.
  - **Trilha B** (metodologia, estatística, escrita): só sugestões, calibradas pelo nível do trabalho.
  - Problemas metodológicos com viés ético passam para a Trilha A (PROJ-G05).
- `base-conhecimento/`: 274 requisitos com ID estável, construídos a partir de 12 documentos do CEP-UMC, da CONEP e da
  Plataforma Brasil. Inclui as divergências entre os documentos, o checklist consolidado, os padrões de erro, o guia do
  tutor e o texto integral das fontes.
- `base-academica/` (versão inicial): 42 sugestões com núcleo comum e nível mínimo, a tabela de diretrizes EQUATOR por
  desenho e as expectativas e o tom por nível.
- `extract.py`:
  - `.docx` lido direto do XML, com tabelas, cabeçalhos, rodapés e campo de página;
  - detecção de trechos em vermelho ou azul (cores dos modelos) e de texto oculto;
  - `.doc` (Word 97) pela tabela de peças;
  - PDF por pdftotext ou pypdf.
- `classify.py`:
  - tipo de cada documento;
  - triagem Q1–Q21, ignorando os critérios de exclusão;
  - nível do trabalho a partir da capa;
  - documentos esperados × recebidos.
- `checks.py`: sinais automáticos derivados dos padrões de erro e verificações de consistência entre documentos, com
  trecho citado no texto original.
- `cep_tutor.py`:
  - `prepare`, `next`, `run` (headless por `claude -p`, `agy -p` ou `gemini -p`) e `compile`;
  - severidade tirada da base;
  - IDs desconhecidos e sinais não verificados listados à parte;
  - classificação Essencial × Para aprofundar por regra, com corte em 5 itens na graduação;
  - alerta para sugestões redigidas como exigência do CEP;
  - avaliações antigas movidas para `superseded/` quando a entrada muda.
- Relatório em Markdown e PDF: Parte 1 (CEP), Parte 2 (sugestões, com aviso de que não são exigências), resumo para o
  orientador, integridade e método.
- Consulta à base (`kb.py search` e `kb.py show`) e modo carta-resposta a pendências.
- Subagente `cep-reviewer`, regras, `install.sh` (marketplace `labiomics`), CI, testes com protocolo fictício.
