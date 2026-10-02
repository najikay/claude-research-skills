---
name: citation-check
description: Verify that each citation in a draft exists, matches the bibliography entry and supports the sentence it is attached to. Use before submitting or sharing a paper, report or thesis section, or when asked whether the references are real.
---

# Citation check

Input: a draft (`.md`, `.tex`, `.docx` text) and its bibliography (`.bib` or a reference list). Ask for the bibliography if only the draft was given.

## Checks, in order
1. **Resolvable**: every `\cite{key}` / `[n]` / (Author, year) maps to exactly one bibliography entry; list orphans both ways (citations without an entry, entries never cited).
2. **Real**: when the `reference-lookup` tools are available, call `verify_bibtex` on the whole bibliography (or `verify_reference` per entry) and report its verdict per entry: `verified`, `mismatch` (with the reason: wrong first author, title or year), `not_found` or `unchecked`. A `not_found` entry is the classic sign of an invented reference; say so plainly. Without the tools, judge from the entry alone (venue fits the title, plausible year, a DOI prefix that looks real) and mark the result `unchecked`.
3. **Support**: for each cited sentence, state what the source must contain for the citation to be fair. When the source text is available (a note, the PDF, a page you can fetch), mark `supported` / `partial` / `not found` with the page or section. When it is not available, mark `unverified`, never `supported`.
4. **Style**: one consistent format, no duplicate entries, arXiv preprints that have a published version (`lookup_reference` on the arXiv id shows the DOI when one exists).

## Output
A table `key · where used · real · supported · style · note`, then a short list of what to fix first: invented or not-found references and orphans before style. Never invent a DOI, page number or quote; "not found" is an answer.

## With the reference-lookup tools
- `verify_bibtex` for a whole `.bib`; `verify_reference` for one entry; `lookup_reference` to clean up an entry from its DOI or arXiv id; `search_works` when a reference is too vague to check; `citation_neighbours` to see what a key paper cites and who cites it.
- The tools send only the reference's title, DOI or arXiv id to OpenAlex and arXiv, two public keyless services. Say which entries were checked that way.
