---
id: guia-para-o-tutor
titulo: Guia de uso da base pelo plugin tutor (fluxo de avaliação pré-submissão)
tipo: guia
aplica_a: [desenvolvimento do plugin]
atualizado: 2026-11-25
---

# Guia para o tutor de pré-submissão

## Papel do tutor
- **Educativo e formativo**, como o próprio CEP (Regimento, art. 4º): explicar **por que** cada requisito existe e **onde**
  ele está nas normas, e não só apontar o erro.
- **Não emite parecer** nem prevê aprovação. Use expressões como "pode gerar pendência", "o CEP costuma exigir", "segundo
  o modelo do CEP-UMC".
- **Não reescreve o projeto pelo pesquisador** sem que ele peça. Prefira mostrar o trecho, o problema, o requisito (ID) e
  uma sugestão.
- **Separa ética de qualidade acadêmica.** Esta base cobre só a **Trilha A** (exigências do CEP). Sugestões de
  metodologia, escrita e estatística são da **Trilha B**: vão em parte separada do relatório, com o rótulo [SUGESTÃO], e
  nunca são apresentadas como exigência do CEP. A regra de fronteira (PROJ-G05) está em `PLANO-DO-PLUGIN.md`.
- Quando a resposta **não estiver na base**, dizer isso e indicar o CEP-UMC (cep@umc.br, (11) 4798-7085) ou o orientador.

## Fluxo de avaliação recomendado

1. **Triagem** (`15-matriz-documentos-por-tipo-de-estudo.md`): identificar o tipo de estudo, a população, a forma de
   consentimento, os locais e o financiamento, e montar a **lista de documentos esperados**.
2. **Inventário**: comparar os documentos recebidos com a lista esperada e apontar os **faltantes** primeiro.
3. **Consistência cruzada** (checklist, bloco A): título, pesquisador, equipe, locais, amostra, cronograma e orçamento
   iguais em todos os documentos; procurar **restos de modelo**.
4. **Projeto** (`03`): seções obrigatórias da NO 001/13 e do modelo; atenção especial a **riscos, benefícios,
   critérios, cronograma e orçamento**.
5. **TCLE / TALE** (`04`–`07`): forma (convite, vias, rubricas) e os itens de conteúdo (TCLE-C01 a C26); conferir com os
   17 direitos (`14`).
6. **Documentos complementares** (`08`–`10`): dispensa, TAI, carta de anuência.
7. **Plataforma Brasil** (`11`): lembretes de cadastro, folha de rosto e nomes de arquivo.
8. **Padrões de erro** (`17`): varredura textual.
9. **Relatório, Parte 1 (ética/CEP)**: ordenar por severidade (BLOQUEANTE → PENDÊNCIA → RECOMENDAÇÃO), cada item com
   **ID**, **trecho**, **por que importa** e **como corrigir**. Terminar com os **próximos passos** e um **lembrete de
   prazos** (`12`).
10. **Relatório, Parte 2 (sugestões acadêmicas)**: metodologia, escrita e estatística, com o rótulo [SUGESTÃO], abrindo
    com o aviso de que esses itens não são cobrados pelo CEP (ver `PLANO-DO-PLUGIN.md`).

## Formato sugerido de achado

```
[PENDÊNCIA] PROJ-M05 — Critério de exclusão é a antítese do de inclusão
Onde: Projeto, p. 8, "Critérios de exclusão: menores de 18 anos."
Por quê: o CEP-UMC orienta que a exclusão trata de quem JÁ atende à inclusão mas tem um impeditivo
         (Modelo de projeto CEP-UMC, v4/2022, item Metodologia 5).
Sugestão: remover este item ou substituí-lo por um impeditivo real (ex.: "participantes com diagnóstico de X").
```

## Mapa de recuperação (pergunta → arquivo)

| Intenção do usuário | Arquivo(s) |
|---|---|
| "Que documentos preciso enviar?" | 15, 11 (PB-D) |
| "Revise meu projeto" | 03, 16 (A e B), 17 |
| "Revise meu TCLE" | 04 (ou 05/06/07), 14, 17 |
| "Estudo com crianças" | 06, 15 |
| "Pesquisa online / Google Forms" | 05, 03 (PROJ-N08) |
| "Pesquisa com prontuários" | 08, 09 |
| "Coleta de sangue, saliva, dente…" | 07 |
| "O que é TAI / quem assina?" | 09 |
| "Prometi atendimento psicológico" | 10 |
| "Recebi pendência, como responder?" | 12 (RESP) |
| "Quero mudar o projeto aprovado" | 13 (EMD) |
| "Projeto não aprovado" | 13 (REC), 12 |
| "Quanto tempo demora?" / cronograma | 12, 03 (PROJ-C13) |
| "Como cadastrar na Plataforma Brasil?" | 11 |
| "Quem é o CEP-UMC / contatos?" | 01 |
| "O que diz a Res. 466 sobre…?" | 02 (apenas trechos citados) |
| Termos e siglas | 18 |
| Divergências entre modelos | 00 |

## Convenções de ID

| Prefixo | Domínio | Arquivo |
|---|---|---|
| `GER-` | Consistência geral entre documentos | 16 |
| `PROJ-G/N/E/P/C/M/R/B` | Projeto: gerais, NO 001/13, específicos, pré-textuais, corpo, metodologia, riscos, benefícios | 03 |
| `TCLE-F/C` | TCLE: forma e conteúdo | 04 |
| `TCLEV-` | TCLE em ambiente virtual | 05 |
| `TALE-`, `TALE-T`, `TALE-R` | Processo de assentimento, TALE, TCLE do responsável | 06 |
| `AMOS-` | Amostra biológica | 07 |
| `DISP-`, `DISP-C` | Dispensa de TCLE | 08 |
| `TAI-` | Termo de Autorização Institucional | 09 |
| `ANU-` | Carta de anuência para assistência gratuita | 10 |
| `PB-U/S/D` | Plataforma Brasil: usuário, submissão, documentos | 11 |
| `RESP-` | Carta-resposta | 12 |
| `EMD-`, `REC-` | Emendas, recursos | 13 |
| `DIR-` | Direitos dos participantes | 14 |

Os IDs são **estáveis**: ao atualizar a base, não renumere; acrescente novos IDs ao final e marque os obsoletos como
`(revogado em AAAA-MM-DD)`.
