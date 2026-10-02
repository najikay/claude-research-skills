---
name: citation-check
description: Verify that each citation in a draft exists, matches the bibliography entry and supports the sentence it is attached to. Use before submitting or sharing a paper, report or thesis section, or when asked whether the references are real.
---

# Citation check

Input: a draft (`.md`, `.tex`, `.docx` text) and its bibliography (`.bib` or a reference list). Ask for the bibliography if only the draft was given.

## Checks, in order
1. **Resolvable**: every `\cite{key}` / `[n]` / (Author, year) maps to exactly one bibliography entry; list orphans both ways (citations without an entry, entries never cited).
2. **Entry sanity**: authors, year, venue and title present; a DOI or arXiv id when one exists. Flag entries that look generated: a venue that does not fit the title, an impossible year, a first author who never worked on the topic, a DOI whose prefix does not match the publisher.
3. **Support**: for each cited sentence, state what the source must contain for the citation to be fair. When the source text is available (a note, the PDF, a web page you can fetch), mark `supported` / `partial` / `not found` with the page or section. When it is not available, mark `unverified`, never `supported`.
4. **Style**: one consistent format, no duplicate entries, arXiv preprints that have a published version.

## Output
A table `key · where used · check · verdict · note`, then a short list of what to fix first: orphans and `not found` before style. Never invent a DOI, page number or quote; say "not found" instead. When you can look references up (a DOI resolver, OpenAlex, Crossref, arXiv), do so for every entry and report what the lookup returned, not what the draft claims.
