# Changelog

## 0.4.2 — 2026-10-13
- **First use lands.** Every skill now ends its reply on one `Next:` line with the words to type next, and leaves something to keep:
  - citation-check: the fix list is a checklist to tick, in order (invented, orphans, mismatches, unverified support, style), plus a block of corrected entries rebuilt only from records it actually looked up; next, re-check after fixing.
  - research-litnote: a `Keep:` line (the file name, or the name to save the block under) and a `Next:` toward the next paper, paper-compare or related-work.
  - paper-compare: the "which to cite for what" lines again as a block to paste.
  - related-work: the draft as one block ready to paste; the `[citation needed]` list as a checklist with search phrases.
  - paper-critique: the three changes that matter most as a checklist; next, revise one and ask for that section to be reviewed again.
  - decision-matrix: a decision record to keep (`chosen:` empty, `revisit:` dated only if you gave a date); next, the reversible first step, and "rescore this" when something changes.
  - llm-council: the claims still to verify as a checklist.
- decision-matrix is described for methods, tools, datasets, designs and plans, no longer job offers (Career Desk compares offers).
- The README says what to type first.
- paper-compare says nothing from memory about a paper it has no text for, in the recommendation either; related-work's search phrases are never a known paper's title; citation-check's corrected entries never put a mismatched paper in place of the user's.
- **Evals re-based.** Each case's long checklist grader is split into single-check graders that restate the facts they check, plus one that the reply ends on a `Next:` line; a test checks that every skill asks for one. 0.4.1 and 0.4.2 were run side by side on the new graders (README); the earlier 1.00 figures are withdrawn.

## 0.4.1 — 2026-10-06
- The hosted checker has two hard ceilings for the whole service: 120 messages a minute in all and 3,000 tool calls a day; past them it refuses with a plain message (citation-check then falls back to web search). The health endpoint shows the day's count.

## 0.4.0 — 2026-10-06
- **The checker everywhere.** The reference checker now also runs as a hosted service (`research-desk-checker.fly.dev`), declared in the plugin beside the local one, so citation-check verifies references in the Claude apps, where 81 % of installs are. Same code, stateless, nothing stored, a rate limit per client; `hosting/` has the Dockerfile and the Fly config to run your own copy.
- A reference whose title OpenAlex cannot verify is searched again filtered to its year, then on arXiv by title: OpenAlex lists a 2025 reprint of *Attention Is All You Need* in place of the 2017 paper, which came back `partial`; it is now `verified` from arXiv.
- Tools carry a title and read-only annotations, so Claude can call them without a prompt per call.
- The eval case `citation-check-tools` was run once against the real hosted server (five lookups over the network): all five checks passed.

## 0.3.1 — 2026-10-05
- A privacy statement (`PRIVACY.md`), linked from the README and the manifest: what the plugin reads, the two public services the reference checker calls, and that nothing is collected.
- A new eval case, `citation-check-tools`, runs citation-check with the reference checker's tools answered by a recorded stand-in, so the route that uses the tools is tested too (the other cases run with no tools). No skill or server code changed.

## 0.3.0 — 2026-10-05
- Three new skills: **paper-compare** (papers side by side, no ranking across different benchmarks), **related-work** (a section drafted only from your own sources, with `[citation needed]` where one is missing) and **paper-critique** (a referee's read of your draft: claims against evidence, ranked, with fixes).
- Every skill is now complete in the Claude apps, where the bundled reference checker cannot run: citation-check verifies through web search when it is on and marks references `unchecked` otherwise, never `verified` from memory; notes and decisions come in the reply when there are no files to write.
- Skill descriptions rewritten in the words people use ("are these references real?", "review my draft"), each saying when the skill does not apply.
- llm-council says which kind of council it ran, and treats agreement between stances of one model as weaker than agreement between models.
- A test that every skill's frontmatter is valid YAML (an unquoted colon in a description silently drops the whole frontmatter).

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
