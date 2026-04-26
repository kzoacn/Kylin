# Kylin Submission EN->ZH Sync Guide

This guide defines the maintenance workflow for the bilingual submission document.

## Source of Truth

- English is the only source of truth.
- The English entrypoint is `main.tex`.
- The Chinese entrypoint is `main_zh.tex`.
- Expected outputs are `main.pdf` and `main_zh.pdf`.

## File Mapping

| English source | Chinese mirror |
| --- | --- |
| `paper/tex/intro.tex` | `paper/tex-zh/intro.tex` |
| `paper/tex/construction.tex` | `paper/tex-zh/construction.tex` |
| `paper/tex/kylin.tex` | `paper/tex-zh/kylin.tex` |
| `paper/tex/design_rationale.tex` | `paper/tex-zh/design_rationale.tex` |
| `paper/tex/security_statements_and_analyses.tex` | `paper/tex-zh/security_statements_and_analyses.tex` |
| `paper/tex/performance_evaluation.tex` | `paper/tex-zh/performance_evaluation.tex` |
| `paper/tex/feature_statements.tex` | `paper/tex-zh/feature_statements.tex` |
| `paper/tex/kylin-appendix.tex` | `paper/tex-zh/kylin-appendix.tex` |
| `paper/figure/sha256-simple-comp.tex` | `paper/figure-zh/sha256-simple-comp.tex` |
| `paper/tex/defs.tex` | `paper/tex/defs_zh.tex` |

## Translation Boundary

- Translate: titles, headings, prose, captions, theorem-like names, TOC/list labels, and cross-reference names.
- Do not translate: formulas, labels, citation keys, code identifiers, file paths, instance names, table numbers, raw metric values, and CSV source references.
- Preserve the structure and ordering of sections, figures, tables, algorithms, and appendices unless the English source changes first.

## Build Commands

- English: `make -C paper/build all`
- Chinese: `make -C paper/build zh`
- Convenience target from the repository root: `make paper-zh`

## Update Workflow

1. Edit the English source first.
2. Identify the mirrored Chinese files affected by the English diff.
3. Copy over any structural changes before polishing wording.
4. Translate only the natural-language layer; keep formulas, labels, metrics, and identifiers untouched.
5. If a new recurring term appears, update `docs/en-zh-glossary.md`.
6. Rebuild both PDFs after medium-sized document changes.
7. Record the result in `plan.md`.

## Review Checklist

- Section and subsection ordering still matches the English document.
- Table values, parameter tuples, instance names, and formulas are unchanged.
- Cross-references render in Chinese and point to the correct targets.
- Bibliography, minted code blocks, and appendix content still compile.
- Any new figure or table fragment has either a Chinese mirror or an explicit reason to stay shared.

## Environment Dependencies

- XeLaTeX
- `texlive-lang-chinese`
- `fonts-noto-cjk`
- `latexmk`
- `python3-pygments`

The repository records these as environment dependencies only. Do not vendor third-party fonts or TeX packages unless explicitly requested.
