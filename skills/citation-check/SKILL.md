---
name: citation-check
description: "Check whether the references in a draft are real and whether each citation supports the sentence it is attached to. Every entry is looked up; invented, mismatched and orphaned references are flagged. Use when the user asks \"are these references real?\", \"check my citations\" or \"check my bibliography\", shares a reference list from AI-written text, or is about to submit a paper, thesis or report. Not for formatting a bibliography in a citation style."
---

# Citation check

Input: a draft and its bibliography (a `.bib`, a reference list, or references pasted in the conversation). Ask for the bibliography if only the draft was given. A reference list alone is fine: then skip the checks that need the draft.

## Checks, in order
1. **Resolvable**: every `\cite{key}` / `[n]` / (Author, year) maps to exactly one bibliography entry; list orphans both ways (citations without an entry, entries never cited).
2. **Real**: look every entry up, by the best means you have (next section), and give each a verdict: `verified` (title, first author and year agree with a record you found), `partial` (title agrees; the year is off or the authors differ in part: show the record), `mismatch` (the DOI or arXiv id leads to another paper, or the first author or title is wrong), `not_found` (you searched and nothing matches) or `unchecked` (you could not look it up).
3. **Support**: for each cited sentence, state what the source must contain for the citation to be fair. When the source text is available (a note, the PDF, a page you can open), mark `supported` / `partial` / `not found` with the page or section. When it is not available, mark `unverified`, never `supported`.
4. **Style**: one consistent format, no duplicate entries, preprints that have a published version.

## How to look an entry up, by what you have
Use the first that applies, and say at the top of the report which one you used.

1. **The `reference-lookup` tools** (Claude Code, Cowork): `verify_bibtex` on a whole `.bib`, `verify_reference` per entry, `lookup_reference` to clean an entry from its DOI or arXiv id, `search_works` when an entry is too vague, `citation_neighbours` for what a paper cites and who cites it. Report the tool's verdict per entry.
2. **Web search or page fetch, no lookup tools** (most chat sessions): for each entry search the exact title in quotes with the first author's surname; when the entry has a DOI open `https://doi.org/<doi>`, when it has an arXiv id open `https://arxiv.org/abs/<id>`. Compare title, first author and year with what you find and give the same verdicts. With more than 25 entries, check first the ones that carry the draft's main claims, then as many as you can, and list the ones left `unchecked`.
3. **Neither**: every entry is `unchecked`. Still report what you can see in the entry itself (a venue that does not fit the title, an impossible year, a malformed DOI), tell the user that opening `https://doi.org/<doi>` is the quickest check of their own, and say that with web search turned on you can do the lookups.

Recognising a title is not a check. From memory alone the most you may say is "recognised, unchecked".

A `not_found` entry with a specific title is the classic sign of an invented reference: say so plainly. Treat a generic title, a non-English title or an `unchecked` result as "could not confirm", not as invented.

## Output
Give the result in the reply; write a file only when the user is working in files and asks for one.

A table `key · where used · real · supported · style · note`, then a short list of what to fix first: invented or not-found references and orphans before style. Never invent a DOI, a page number or a quote; "not found" is an answer.

## What leaves the conversation
The lookup tools send an entry's title, DOI or arXiv id (and for `search_works` the search words you compose) to OpenAlex and arXiv, two public keyless services. Web search sends the same kind of query to the search provider. Do not put sentences from the user's draft into a search.
