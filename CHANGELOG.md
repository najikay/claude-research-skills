# Changelog

## 0.2.1 — 2026-10-03
- Reference lookup: a DOI or arXiv id that resolves to another paper is reported as a mismatch (it was silently passed over).
- Titles with accents, LaTeX accents (`{\"u}`) or non-Latin scripts are matched (they were never found).
- A `partial` verdict: title agrees but the year is off or no authors were given.
- The server survives any input (non-object messages, bad params), writes UTF-8 on every platform, paces arXiv at one call per three seconds, retries once on 429/503, times out per request and per batch.
- BibTeX: nested braces, `@string` macros, `@comment`/`@preamble` skipped, duplicate citekeys flagged, one bad entry never spoils the batch.
- arXiv lookups return the DOI when arXiv records one; `refs: 0` / `cites: 0` are honoured.

## 0.2.0 — 2026-10-02
- `reference-lookup` MCP server (standard-library Python): verify a reference or a whole BibTeX against OpenAlex and arXiv, look up metadata, search works, citation neighbours.
- `citation-check` uses it; harder eval; offline tests and CI.

## 0.1.0 — 2026-10-02
- Four skills: citation-check, research-litnote, decision-matrix, llm-council. Evals, Apache-2.0.
