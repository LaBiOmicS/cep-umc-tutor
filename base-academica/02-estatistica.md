---
id: estatistica
titulo: Sugestões de estatística (Trilha B)
tipo: sugestoes
aplica_a: [projeto de pesquisa, estudos quantitativos]
status: versão inicial, a validar pela equipe
atualizado: 2026-11-25
---

# Estatística

> A Trilha A já verifica se o projeto **informa** quantos participantes e como chegou ao número (PROJ-M02) e se **tem**
> plano de análise (PROJ-C07). Aqui entra a **adequação técnica** desses elementos.

| ID | Sugestão | Núcleo comum | Nível mínimo | Por que importa | Fonte / para estudar |
|---|---|---|---|---|---|
| SUG-EST-01 | O **tamanho da amostra** tem uma justificativa que se sustenta (cálculo, população inteira acessível, ou viabilidade declarada como limitação). | sim | graduação | Amostra sem justificativa não permite saber se o estudo responde à pergunta. | Miot, *J. Vasc. Bras.*, 2011 (tamanho da amostra); STROBE, item 10 |
| SUG-EST-02 | (Objetivo inferencial) **Cálculo amostral formal**: teste previsto, tamanho de efeito e sua fonte, α, poder, perdas previstas e software. | não | mestrado | Sem esses parâmetros, o cálculo não pode ser conferido nem reproduzido. | CONSORT, item 7a; G*Power (manual) |
| SUG-EST-03 | O **teste estatístico é compatível** com o tipo de variável e com o desenho (ex.: pareado × independente; categórico × contínuo; dois × mais grupos). | sim | graduação | Teste inadequado gera conclusões erradas, mesmo com dados corretos. | SAMPL (Lang e Altman, 2013); tabelas de escolha de testes de livros de bioestatística |
| SUG-EST-04 | **Estatística descritiva adequada** à distribuição: média e desvio-padrão para dados simétricos; mediana e intervalo interquartil para assimétricos; frequências para categóricos. | sim | graduação | Resumo inadequado distorce a descrição da amostra. | SAMPL |
| SUG-EST-05 | **Nível de significância e software** declarados no plano de análise. | não | graduação | Permite a reprodução da análise. | SAMPL; STROBE, item 12 |
| SUG-EST-06 | **Pressupostos** dos testes (normalidade, homogeneidade de variâncias, independência) e como serão verificados, com alternativa não paramétrica prevista. | não | especialização | Violação de pressupostos invalida o teste escolhido. | SAMPL |
| SUG-EST-07 | (Escalas tipo Likert) Tratamento justificado: item como variável **ordinal**; escore somado só quando a escala validada o permite. | não | especialização | Tratar item ordinal como contínuo sem justificativa é erro frequente. | Manual da escala utilizada |
| SUG-EST-08 | Interpretar resultado **não significativo** como "não houve evidência de diferença", e **não** como "não há diferença" ou "os grupos são iguais". | sim | graduação | Ausência de evidência não é evidência de ausência. | Wasserstein e Lazar, *Am. Stat.*, 2016 (declaração da ASA sobre o valor de p) |
| SUG-EST-09 | Prever **tamanho de efeito e intervalo de confiança**, além do valor de p. | não | mestrado | O p sozinho não informa a magnitude nem a precisão do efeito. | Declaração da ASA, 2016; CONSORT, item 17 |
| SUG-EST-10 | Plano para **comparações múltiplas** (correção ou hierarquia de hipóteses). | não | mestrado | Muitos testes sem correção inflam os falsos positivos. | SAMPL |
| SUG-EST-11 | **Modelo multivariado** justificado: variáveis de ajuste escolhidas por critério teórico (ex.: diagrama causal), não só por p na análise bivariada. | não | mestrado | Seleção automática de covariáveis produz modelos instáveis e viesados. | STROBE, item 12; literatura de DAGs em epidemiologia |
| SUG-EST-12 | **Unidade de análise** e dados correlacionados tratados (medidas repetidas, pacientes dentro de serviços, dentes dentro de bocas). | não | mestrado | Ignorar a correlação subestima o erro-padrão. | SAMPL; livros de modelos mistos |
| SUG-EST-13 | **Análise de sensibilidade** para as principais suposições (dados faltantes, definição de desfecho). | não | doutorado | Mostra se a conclusão depende de escolhas analíticas. | SPIRIT, item 20 |
| SUG-EST-14 | Não usar linguagem **causal** ("comprova", "causa", "leva a") quando o desenho só permite associação. | sim | graduação | Superestimar a evidência é erro de interpretação, não de estilo. | STROBE, item 20 |
