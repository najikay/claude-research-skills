# Research Desk

![Research Desk](assets/banner.png)

[![tests](https://github.com/najikay/claude-research-skills/actions/workflows/tests.yml/badge.svg)](https://github.com/najikay/claude-research-skills/actions/workflows/tests.yml)

**Research work you can stand behind.** Seven skills for the things a student or researcher does every week: check that references are real, take faithful notes on a paper, compare papers, draft related work from your own sources, get your draft reviewed before a referee does, decide between options, and get a second opinion. Plus a small reference checker that looks papers up in OpenAlex and arXiv.

**Try it first:** paste your reference list and type *Are these references real?* Or attach a PDF and type *Make notes on this paper.*

The skills share one habit: **they say what they could not check.** A reference is `verified` only when it was looked up; a claim is `supported` only when the source text was read; a missing citation becomes `[citation needed]`, never an invented one.

## The skills

| Skill | Say something like | What you get |
|---|---|---|
| **citation-check** | "Are these references real?" "Check my citations before I submit." | A table per citation: does it resolve, is the reference real (`verified`, `partial`, `mismatch`, `not_found`, `unchecked`), does the source support the sentence, style. Orphans both ways. A fix list to tick, and corrected entries rebuilt from the records it found. |
| **research-litnote** | "Summarise this paper." "Make notes on this PDF." | A structured note: one-line takeaway, problem, method, evidence with page references, limits, quotes. Marked with what it was based on (full text or abstract only). |
| **paper-compare** | "Compare these three papers." "Which should be my baseline?" | A side-by-side table with the numbers copied from each paper and where they stand, what each adds, which to cite for what, and a plain "not directly comparable" when benchmarks differ. |
| **related-work** | "Draft my related work from these notes." | A themed section where every sentence carries one of *your* sources, ending on the gap your work fills, with a list of every `[citation needed]`. |
| **paper-critique** | "Review my draft." "What will reviewers say?" | Each claim against its evidence, missing baselines and ablations, statistical weak points, threats to validity, ranked with a concrete fix each, and the three changes that matter most. |
| **decision-matrix** | "Help me decide between these two methods." | Options against weighted criteria with a reason per score, what would flip the result, a recommendation and a reversible first step, as a decision record you keep. The decision stays yours. |
| **llm-council** | "Give me a second opinion." "Argue both sides." | Several independent answers, then a judge: agreements, disagreements, claims to verify, a final answer with a confidence. |

## Where it runs

| | Claude apps (web, desktop, mobile) | Claude Code and Cowork |
|---|---|---|
| The seven skills | yes | yes |
| Looking references up | through the hosted reference checker (the same checker, served from `research-desk-checker.fly.dev`); web search as the fallback | through the bundled reference checker (below); needs Python 3.10+, see Platforms |
| Saving notes as files | the note comes in the reply, ready to copy | saved in the folder you choose |

Without web search and without the checker, citation-check still finds orphans and suspicious entries, flags claims it cannot check as `unverified`, and marks every reference `unchecked` instead of guessing.

## The hosted checker

Since 0.4 the checker also runs as a small web service, so references are verified in the Claude apps too. In Claude Code and Cowork both copies are available (`reference-lookup` on your machine, `reference-lookup-hosted` on the web); they have the same five tools, and the local one works offline. It is the same code (`servers/reference_lookup/remote.py` wraps `server.py` in MCP's Streamable HTTP transport), stateless, with nothing stored and a rate limit per client; see `hosting/README.md` to run your own copy. What it receives and where it goes is in [PRIVACY.md](PRIVACY.md).

## The reference-lookup server

`servers/reference_lookup/server.py` is a stdio MCP server in standard-library Python (3.10+, no packages to install). It gives Claude five tools:

| tool | what it does |
|---|---|
| `verify_reference` | one reference (title, authors, year, DOI, arXiv id) → `verified` (title, first author, year agree) / `partial` (title agrees; year off or no authors given) / `mismatch` (wrong author or title, or an identifier that points elsewhere) / `not_found` / `unchecked`, with the matched record and the reasons |
| `verify_bibtex` | the same for every entry of a `.bib` text, with counts |
| `lookup_reference` | clean metadata for a DOI, arXiv id or OpenAlex id |
| `search_works` | candidate papers for a few search words (OpenAlex searches titles, abstracts and full text) |
| `citation_neighbours` | what a paper cites and the most-cited papers citing it |

It asks two public, keyless services: [OpenAlex](https://openalex.org) (works by DOI or title) and [arXiv](https://arxiv.org) (arXiv ids), one request at a time, with arXiv's one-call-per-three-seconds rule respected. There is no account, key or storage.

**Data handling** (the full statement is in [Privacy](PRIVACY.md))**.** The server itself never sees your draft; Claude passes it a reference's title, DOI or arXiv id, or a few search words for `search_works`. Those go to `api.openalex.org` and `export.arxiv.org`, which see the request as any web request (your address, the plugin's user agent). Nothing is kept by the plugin. No personal data is read or stored. Author names in a bibliography are public bibliographic data and are sent only to match the paper.

In the Claude apps the checker does not run. There, citation-check looks references up through Claude's web search, which sends a reference's title, DOI or arXiv id as a search; related-work may search a topic phrase for a missing citation. Neither sends sentences from your draft or a description of your unpublished work.

**Platforms.** Python 3.10 or newer on the PATH as `python3` (on Windows, install Python from python.org and tick "Add to PATH"; if only `python` exists, change the command in `.mcp.json`).

## Install

From the Claude directory: search for Research Desk. In Claude Code:

```
/plugin marketplace add najikay/claude-research-skills
/plugin install research-desk@claude-research-skills
```

## Tests and evals

- `python -m pytest -q` runs the reference checker's offline tests (every HTTP call replaced by a fake), a check that every skill's frontmatter is valid, and a check that every skill ends its reply on a `Next:` line; CI runs them on Linux and Windows.
- `evals/` holds one case per skill: a prompt with a small inlined draft, bibliography or paper excerpt, and graders that each check one thing and restate the facts they check (the judge sees only the answer). One grader per case checks that the reply ends on a `Next:` line. `claude plugin eval .` runs each case with the plugin and without it.
- `evals/citation-check-tools` is the one case that uses the reference checker's tools; a stand-in answers the tool calls from recordings (`mocks/`), so the run needs no network. On 2026-10-06 it also passed once against the real hosted checker.

The graders were rewritten on 2026-10-13 (each case's single long checklist split into one check per grader), so the numbers below are re-based and replace the earlier 1.00 figures, which do not reproduce under the new graders or the current Claude Code. Last run: Claude Code 2.1.291, judge Sonnet, three runs per case and version, 2026-10-13. "All checks" is the number of runs that passed every grader of the case; "share" is the mean share of graders passed.

| Case (graders) | 0.4.2 all checks | 0.4.2 share | 0.4.1 all checks | 0.4.1 share | No plugin share |
|---|---|---|---|---|---|
| citation-check (10) | 3/3 | 1.00 | 0/3 | 0.87 | 0.47 |
| citation-check-tools (6) | 2/3 | 0.90 | 0/3 | 0.86 | 0.38 |
| decision-matrix (11) | 2/3 | 0.97 | 0/3 | 0.76 | 0.27 |
| llm-council (11) | 3/3 | 1.00 | 0/3 | 0.91 | 0.52 |
| paper-compare (13) | 1/3 | 0.95 | 0/3 | 0.87 | 0.56 |
| paper-critique (14) | 0/3 | 0.88 | 0/3 | 0.79 | 0.52 |
| related-work (10) | 0/3 | 0.80 | 0/3 | 0.67 | 0.30 |
| research-litnote (7) | 1/3 | 0.90 | 0/3 | 0.71 | 0.38 |

0.4.1 has no `Next:` line, so it fails that grader in every run; leaving that grader out, 0.4.1 passes all checks in 2/3 (citation-check), 3/3 (citation-check-tools), 0/3, 3/3, 2/3, 0/3, 0/3 and 0/3 runs, and 0.4.2 in 3/3, 2/3, 2/3, 3/3, 1/3, 0/3, 0/3 and 1/3. Of the misses we read, several are strict readings of right answers (a critique that first says what it was given fails "opens with how the paper reads"; a correct comparison table failed once); the related-work check that every sentence about prior work carries a source fails for both versions in every run. The no-plugin column passes all checks in no run.

Each case is built so that a plausible-sounding answer fails: a reference list with an invented entry and an orphan, papers on two different benchmarks plus one given by title only, a related-work request that tempts a citation from memory, a draft that claims significance from one run.

## Author

Naji Kayal, University of Haifa (robotics, SLAM, computer vision). Issues and suggestions are welcome here.

## License

Apache-2.0. See `LICENSE`. See `CHANGELOG.md` for versions.
