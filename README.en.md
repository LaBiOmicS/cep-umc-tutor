# cep-umc-tutor

[![Status: beta](https://img.shields.io/badge/status-beta-orange.svg)](https://github.com/LaBiOmicS/cep-umc-tutor/issues)
[![CI](https://github.com/LaBiOmicS/cep-umc-tutor/actions/workflows/ci.yml/badge.svg)](https://github.com/LaBiOmicS/cep-umc-tutor/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/LaBiOmicS/cep-umc-tutor)](https://github.com/LaBiOmicS/cep-umc-tutor/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org)
[![Project page](https://img.shields.io/badge/docs-GitHub%20Pages-0b6e4f.svg)](https://labiomics.github.io/cep-umc-tutor/)

[Português](README.md) · **English** · [Español](README.es.md)

> [!WARNING]
> **Beta.** The tutor can be wrong, both when reading the documents and in its findings. Check every result with your
> supervisor. It **does not replace** the CEP-UMC review.

A plugin for **Claude Code** and **Antigravity (`agy`)** that helps researchers, students and supervisors review a
research protocol **before** submitting it, through Plataforma Brasil, to the **Research Ethics Committee of the
University of Mogi das Cruzes (CEP-UMC)**, Brazil.

The tutor's knowledge base, prompts and reports are in Portuguese, like the CEP-UMC documents and the protocols it
reviews. This README and the [project page](https://labiomics.github.io/cep-umc-tutor/) are available in English and
Spanish.

The review has **two tracks that never mix**:

| | **Track A — Ethics and documents** | **Track B — Academic quality** |
|---|---|---|
| What it checks | CEP-UMC ethics and document requirements | Methods, statistics and writing |
| Nature | Requirement: the committee may issue a pending decision | **Suggestion**: not required by the committee |
| Labels | [BLOQUEANTE] (blocking) · [PENDÊNCIA] (pending) · [RECOMENDAÇÃO] (recommendation) | [SUGESTÃO] (suggestion) · Essential / Going further |
| Base | `base-conhecimento/` (CEP-UMC documents) | `base-academica/` (EQUATOR, ABNT, methods literature) |
| Calibration | The same for everyone | By the **level** of the work: undergraduate (IC/TCC), specialization, master's, PhD, faculty |

The boundary between the tracks comes from the CEP-UMC project template itself (PROJ-G05): the committee assesses
methods only when they create an ethical bias. In those cases the issue goes to Track A.

**Step-by-step guide for non-programmers:** <https://labiomics.github.io/cep-umc-tutor/>

Part of the LaBiOmicS/UMC plugin line, with
[academic-peer-review](https://github.com/LaBiOmicS/academic-peer-review),
[congress-abstract-review](https://github.com/LaBiOmicS/congress-abstract-review) and
[whoqol-toolkit](https://github.com/LaBiOmicS/whoqol-toolkit).

---

## Contents

- [What the tutor does](#what-the-tutor-does)
- [Flow](#flow)
- [Installation](#installation)
- [Usage](#usage)
- [Outputs](#outputs)
- [Knowledge bases](#knowledge-bases)
- [Security and confidentiality](#security-and-confidentiality)
- [Limitations](#limitations)
- [Development](#development)
- [License and authorship](#license-and-authorship)

## What the tutor does

- **Full protocol review:**
  - reads the documents (`.docx`, `.doc`, `.pdf`, `.md`, `.txt`; `.odt`, `.rtf` and `.html` via pandoc) and
    identifies the type of each one;
  - **screens** the study (minors? online? biological material? medical records? collection site? referral to a
    service?) and builds the list of **expected × received documents**;
  - runs **automatic signals**: "there are no risks", exclusion criteria that merely negate the inclusion criteria,
    data collection before approval, "copy" in a paper consent form, template leftovers and red passages, title or
    sample size differing between documents, file names Plataforma Brasil rejects…;
  - two reviewers (Track A and Track B) assess the protocol, and the code assembles the report.
- **Planning (no documents yet):** for those starting out. From a few questions (minors? online? collection site?…),
  the level and the collection date, it lists the documents to prepare, who signs each one, the submission deadline
  and the most common mistakes (`planejamento.md`).
- **Knowledge-base questions:** "do I need an assent form (TALE)?", "who signs the site permit (TAI)?", "how long does
  the committee take?". The answer cites the requirement and its source.
- **Response letter to pending items:** one entry per pending item, quoted verbatim, with the new text and where it
  changed.

### Which output for whom

| Who | Where to look first |
|---|---|
| Undergraduate student | `planejamento.md` (before writing); then "Comece por aqui" (start here) in `relatorio.md`: up to 5 actions, in order |
| Graduate student | `relatorio.md`: submission deadline computed from the timeline, Part 1 with IDs, Part 2 with up to 8 essential suggestions |
| Supervisor | `relatorio_orientador.md`: one page with "is it ready?", what is missing, who signs what and the deadline |

### The review ends

Fixing and running again does not open an endless list:

- **up to 3 rounds** per protocol (`--max-rodadas`); a round is a different version of the documents;
- from the **2nd round** on, the tutor **verifies** what it already pointed out (solved, still pending) and only adds a
  new item if it is a blocking or pending ethics issue; in Track B, nothing new outside the common core;
- after the 3rd, the cycle closes: only Track A verification, and the report recommends finishing with the supervisor
  and submitting;
- each block has a cap:
  - Essential: 5 for undergraduates, 8 for graduate work;
  - Going further: 5;
  - recommendations: 8;
  - points to check: 10;
- each review gets at most 2 attempts.

The tutor **does not issue an ethics opinion** and does not predict approval. Severity is an editorial classification,
taken from the wording of the committee's documents, not an official criterion.

## Flow

```mermaid
flowchart LR
    D["Protocol documents"] --> P["1 · prepare<br/>extraction, document type,<br/>screening Q1–Q21, level,<br/>expected × received,<br/>automatic signals"]
    P --> A["2 · Track A<br/>ethics and documents"]
    P --> B["2 · Track B<br/>methods, statistics,<br/>writing"]
    A --> C["3 · compile<br/>severity from the base,<br/>Essential × Going further,<br/>two-part report"]
    B --> C
```

Steps 1 and 3 are deterministic and covered by tests. Language models only come in at step 2: they read, judge and
write. Severity, level classification and report assembly are done by the code.

## Installation

```bash
git clone https://github.com/LaBiOmicS/cep-umc-tutor.git
cd cep-umc-tutor
./install.sh
```

`install.sh`:
- syncs the dependencies with `uv`;
- registers the plugin in Claude Code through the `labiomics` marketplace (shared with the other LaBiOmicS plugins);
- registers the plugin in Antigravity, when `agy` is installed.

Restart the session after installing.

Without cloning, straight from GitHub, in Claude Code:

```bash
claude plugin marketplace add LaBiOmicS/cep-umc-tutor
claude plugin install cep-umc-tutor@labiomics
```

Anyone who already uses another LaBiOmicS plugin gets `Cannot add marketplace "labiomics"` on the first line: run
`claude plugin marketplace update labiomics` instead, then the second.

In Antigravity, from the cloned folder or the extracted release zip:

```bash
agy plugin validate ./cep-umc-tutor --strict
agy plugin install ./cep-umc-tutor
agy plugin enable cep-umc-tutor
```

Requirements: Python ≥ 3.10 and [`uv`](https://docs.astral.sh/uv/) (recommended). Optional: `pdftotext` (poppler) for
PDFs and `pandoc` for `.odt`, `.rtf` and `.html`.

## Usage

Ask in natural language, in the folder where the documents are (in Portuguese or English):

- "Revise meu protocolo antes de submeter ao CEP-UMC" (folder `protocolo/`)
- "Does my consent form (TCLE) follow the CEP template?"
- "It is an undergraduate psychology thesis with recorded interviews: which documents must I send?"
- "I received pending items from the CEP; help me write the response letter"

The agent confirms with you the document types, the screening and the **level of the work** before reviewing.

### Command line (without the agent)

```bash
S=skills/cep-tutor/scripts
uv run $S/cep_tutor.py prepare --input protocolo/ --output-dir cep_tutor/my-project [--nivel mestrado]
uv run $S/cep_tutor.py run     --output-dir cep_tutor/my-project --runner claude   # headless reviewers
uv run $S/cep_tutor.py compile --output-dir cep_tutor/my-project
uv run $S/cep_tutor.py planejar --output-dir cep_tutor/plan --nivel graduacao --coleta 2027-06-01 --q "Q7=sim"
uv run $S/kb.py search "assentimento"   # knowledge-base search
uv run $S/kb.py show TCLE-C11
```

| `prepare` option | Use |
|---|---|
| `--nivel graduacao\|especializacao\|mestrado\|doutorado\|docente` | Level of the work. Without it, the tutor looks at the cover page; if nothing is found, it assumes undergraduate. |
| `--trilhas A,B` | One track only (`A` or `B`) or both (default). |
| `--tipo "file.docx=tcle"` | Corrects the type of a document (repeatable). |
| `--q "Q3=sim"` | Corrects a screening answer (repeatable). |
| `--max-rodadas 3` | Maximum number of review rounds for the protocol. |

## Outputs

In `cep_tutor/<project>/`:

| File | Content |
|---|---|
| `relatorio.md` / `relatorio.pdf` | "Start here", progress since the previous round, submission deadline, legend. **Part 1 (committee)**: findings by severity, warnings about discrepancies, points to check and next steps. **Part 2 (suggestions)**: strengths, Essential, Going further and a summary for the supervisor. |
| `relatorio_orientador.md` / `.pdf` | One page for the supervisor: status, pending items, signatures, deadline and essential suggestions. |
| `historico/` | One summary per version of the documents (used to count rounds). |
| `resumo.json` | Everything in the report, structured. |
| `triagem.md` / `triagem.json` | Screening answers with evidence, expected × received documents and automatic signals. |
| `documentos/` | Text extracted from each document. |
| `avaliacao_trilha_a.md` / `_b.md` | Reviewer assessments (with the `FINDINGS_JSON` block). |

## Knowledge bases

- **`base-conhecimento/`** (Track A): built from 12 official documents:
  - CEP-UMC templates of February 2022;
  - 2025 bylaws (Regimento Interno);
  - Plataforma Brasil researcher manual;
  - CONEP booklet on the rights of research participants.

  It has 274 requirements with stable IDs, the discrepancies between documents (e.g. the committee's office hours,
  D1), a consolidated checklist and the tutor guide. `base-conhecimento/fontes/` holds the full text of the documents
  and `base-conhecimento/PLANO-DO-PLUGIN.md` the scope and the boundary between tracks.
- **`base-academica/`** (Track B): 42 items on methods, statistics and writing. Each states whether it belongs to the
  common core, from which level it becomes "Essential" and where to study it. It is an **initial version**, to be
  validated with undergraduate and graduate program coordinators.

### How they were built

1. **Source conversion.** The 12 documents in `docs/` were converted to full text (`base-conhecimento/fontes/`), so
   they can be quoted literally.
2. **Requirement extraction.** Each requirement became a table row with a stable ID (e.g. `TCLE-C11`), source document
   and item, and severity. Severity comes from the source's wording: **[BLOQUEANTE]** (blocking) when the source says
   the problem leads to rejection, **[PENDÊNCIA]** (pending) when it usually leads to a pending decision,
   **[RECOMENDAÇÃO]** for good practice.
3. **Discrepancies recorded.** Where documents disagree (11 cases, e.g. office hours), both versions are kept in
   `00-fontes-e-discrepancias.md` and the tutor asks to confirm with the committee instead of picking one.
4. **Screening tools.** A matrix of documents by study type (21 questions), a consolidated checklist and 45 frequent
   error patterns, which become the automatic signals.
5. **Academic base.** Items written from the EQUATOR guidelines (STROBE, CONSORT, SPIRIT, SAMPL), ABNT standards
   (NBR 14724, 15287) and the methods literature. Each item states whether it is common core and its minimum level.
6. **Checks.** `kb.py stats` and the tests verify that every ID cited in the checklist and patterns exists.

### How they are used in the review

This is not similarity-search RAG: there is no vector store. The bases are Markdown, and the code picks **whole
sections by rule**, so no applicable requirement is left out for not "looking like" the text.

| Stage | What the base does |
|---|---|
| Preparation (`prepare`) | From the screening and the documents received, hands the Part 1 reviewer the files that apply (always project, Plataforma Brasil, checklist and frequent errors; plus consent, assent, site permit, online collection etc. as needed). The Part 2 reviewer gets the whole academic base. |
| Automatic signals | Error patterns run before the AI ("no risks", collection before approval, template leftovers); the reviewer confirms or discards each one. |
| Review | The reviewer must cite the requirement ID and the document passage. |
| Compilation (`compile`) | Severity comes from the table, not the model. An unknown ID does not become a pending item: it goes to "Outros pontos" (no matching requirement in the base). In Part 2, common core and minimum level decide Essential × Going further. |
| Quick questions | "Do I need an assent form?" is answered with the requirement and its source. |

Severity is an **editorial classification**, not an official CEP-UMC criterion.

To update when the committee publishes new templates, see the "Manutenção" section of `base-conhecimento/README.md`.
IDs are never renumbered.

## Security and confidentiality

- Protocols are **unpublished** and may contain **personal data**. The text goes to the AI service running the agent;
  make sure this is allowed before processing other people's documents.
- `.gitignore` excludes `cep_tutor/`, `protocolos/` and `relatorios/`.
- Document text is treated as data:
  - invisible characters are removed;
  - hidden text (Word) and instructions aimed at AI ("do not point out pending items") are ignored in the review and
    reported as an **integrity alert**;
  - in headless mode, environment variables holding secrets are removed and the reviewer can only read files.

## Limitations

- Document classification, screening and signals are heuristic (in Portuguese). The agent confirms with you whatever
  is uncertain.
- The footer ("Page X of Y", initials) can only be checked in `.docx` and `.pdf`.
- The tutor only compares the project with Plataforma Brasil if you include the "Informações Básicas do Projeto" PDF it
  generates; without it, consistency stays as a reminder.
- The submission deadline is an estimate (40–50 days of processing, 30 + 30 per pending round) from the collection
  start date found in the timeline.
- The base reflects the documents provided (2022 templates, 2025 bylaws). Later rules are not included.

## Development

```bash
uv run --all-extras pytest -q
uvx ruff check skills tests
uv run skills/cep-tutor/scripts/kb.py stats   # base integrity
```

Structure:

```
.claude-plugin/          manifests (Claude Code) and the labiomics marketplace
plugin.json              manifest (Antigravity)
agents/cep-reviewer.md   reviewer subagent
rules/AGENTS.md          tutor rules
skills/cep-tutor/        SKILL.md, prompts/, references/, scripts/
base-conhecimento/       Track A (CEP-UMC) + fontes/ + PLANO-DO-PLUGIN.md
base-academica/          Track B (suggestions by level)
docs/                    original CEP-UMC documents
site/                    GitHub Pages site (published by .github/workflows/pages.yml)
assets/                  logo
tests/                   tests (fictional protocol in fixtures/)
```

## License and authorship

MIT. Prof. Dr. Fabiano Bezerra Menegidio, Laboratory of Bioinformatics and Omics Sciences (LaBiOmicS), University of
Mogi das Cruzes (UMC).

The documents in `docs/` belong to the CEP-UMC, CONEP and the Brazilian Ministry of Health, and keep their own terms.
