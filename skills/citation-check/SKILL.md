---
name: citation-check
description: "Check whether the references in a draft are real and whether each citation supports the sentence it is attached to. Each entry is looked up when lookup tools or web search are available and marked unchecked otherwise; invented, mismatched and orphaned references are flagged. Use when the user asks \"are these references real?\", \"check my citations\" or \"check my bibliography\", or wants the references checked before submitting. Not for formatting a bibliography in a citation style."
---

# Citation check

Input: a draft and its bibliography (a `.bib`, a reference list, or references pasted in the conversation). Ask for the bibliography if only the draft was given. A reference list alone is fine: then skip the checks that need the draft.

## Checks, in order
1. **Resolvable**: every `\cite{key}` / `[n]` / (Author, year) maps to exactly one bibliography entry; list orphans both ways (citations without an entry, entries never cited).
2. **Real**: look every entry up, by the best means you have (next section), and give each a verdict: `verified` (title, first author and year agree with a record you found; a year off by one, preprint against proceedings, still agrees), `partial` (the title agrees but the year is off by more than one or the entry gives no authors: show the record), `mismatch` (the DOI or arXiv id leads to another paper, or the first author or title is wrong), `not_found` (you searched and nothing matches) or `unchecked` (you could not look it up).
3. **Support**: for each cited sentence, state what the source must contain for the citation to be fair. When the source text is available (a note, the PDF, a page you can open), mark `supported` / `partial` / `not found` with the page or section. When it is not available, mark `unverified`, never `supported`.
4. **Style**: one consistent format, no duplicate entries, preprints that have a published version.

## How to look an entry up, by what you have
Start with the first that applies, and say at the top of the report which you used. If a route leaves entries `unchecked`, try the next route for those entries.

1. **The `reference-lookup` tools** (Claude Code, Cowork): `verify_bibtex` on a whole `.bib`, `verify_reference` per entry, `lookup_reference` to clean an entry from its DOI or arXiv id, `search_works` when an entry is too vague, `citation_neighbours` for what a paper cites and who cites it. Report the tool's verdict per entry. `verify_bibtex` stops after 60 entries or at its time limit: list any entry it did not reach as `unchecked`, or send the rest in a second call.
2. **Web search or page fetch, no lookup tools** (most chat sessions): for each entry search the exact title in quotes with the first author's surname; when the entry has a DOI open `https://doi.org/<doi>`, when it has an arXiv id open `https://arxiv.org/abs/<id>`. Compare title, first author and year with what you find and give the same verdicts. With more than 25 entries, check first the ones that carry the draft's main claims, then as many as you can, and list the ones left `unchecked`.
   - **What counts as a record**: the paper's own page, at the DOI landing page, the publisher, arXiv, DBLP, ACL Anthology, PubMed, OpenAlex, Crossref or Semantic Scholar. A mention in another paper's reference list, a citation-generator site or a search snippet alone is not a record.
   - Put the record's URL in the note column for every `verified`, `partial` and `mismatch`, so the user can check your check.
   - A page that fails to load, blocks you or asks for a login leaves that entry `unchecked`, not `not_found`.
3. **Neither**: every entry is `unchecked`. Still report what you can see in the entry itself (a venue that does not fit the title, an impossible year, a malformed DOI), tell the user that opening `https://doi.org/<doi>` is the quickest check of their own, and say that with web search turned on you can do the lookups.

An entry is `verified` only if you looked it up in this conversation. Recognising a title is not a check: from memory alone the most you may say is "recognised, unchecked", however famous the paper.

A `not_found` entry with a specific title is the classic sign of an invented reference: say so plainly. Treat a generic title, a non-English title or an `unchecked` result as "could not confirm", not as invented. Red flags in the entry itself (a venue that does not fit the title, a DOI that does not look real, an implausible claim in the title) are reported as `suspicious`, with the reason, even when the entry is `unchecked`.

## Output
Give the result in the reply; write a file only when the user is working in files and asks for one.

A table `key · where used · real · supported · style · note`, then a short list of what to fix first: invented or not-found references and orphans before style. Never invent a DOI, a page number or a quote; "not found" is an answer.

## What leaves the conversation
The lookup tools send an entry's title, DOI or arXiv id (and for `search_works` the search words you compose) to OpenAlex and arXiv, two public keyless services. Web search sends the same kind of query to the search provider. Do not put sentences from the user's draft into a search.
