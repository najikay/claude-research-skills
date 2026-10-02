# Research Desk

![Research Desk](assets/banner.png)

Four skills and one small tool server for research work, as a Claude plugin: the skills tell Claude how to check citations, write literature notes, structure decisions and run a council of independent answers; the `reference-lookup` server lets `citation-check` find out whether a reference is real instead of guessing.

| skill | ask for it when | what you get |
|---|---|---|
| **citation-check** | before sharing a draft | a table per citation: resolvable, **real** (verified / mismatch / not found, via the lookup server), supported by the source or `unverified`, style; orphans both ways; what to fix first; never an invented DOI, page or quote |
| **research-litnote** | you read a paper you will cite | a structured note (takeaway, problem, method, evidence with page refs, limits, relevance, quotes) with frontmatter and a citekey, left as a draft for you to accept |
| **decision-matrix** | you are choosing between alternatives | options × weighted criteria with evidence, a sensitivity check, a recommendation and a reversible first step; the decision stays yours |
| **llm-council** | a judgement call deserves more than one answer | several independent answers, then an anonymised judge: agreements, disagreements, claims to verify, a final answer with confidence |

## The reference-lookup server

`servers/reference_lookup/server.py` is a stdio MCP server in standard-library Python (3.10+, no packages to install). It gives Claude five tools:

| tool | what it does |
|---|---|
| `verify_reference` | one reference (title, authors, year, DOI, arXiv id) → `verified` / `mismatch` / `not_found` / `unchecked`, with the matched record and the reasons (wrong first author, title or year) |
| `verify_bibtex` | the same for every entry of a `.bib` text, with counts |
| `lookup_reference` | clean metadata for a DOI, arXiv id or OpenAlex id |
| `search_works` | candidate papers by words in the title |
| `citation_neighbours` | what a paper cites and the most-cited papers citing it |

It asks two public, keyless services: [OpenAlex](https://openalex.org) (works by DOI or title) and [arXiv](https://arxiv.org) (arXiv ids). Only the reference's own title, DOI or arXiv id leaves your machine; nothing is stored anywhere, and there is no account or key.

**Data handling.** Reads only what you give it (a draft and its bibliography). Sends reference identifiers and titles to `api.openalex.org` and `export.arxiv.org`. Keeps nothing. Does not handle personal data.

## Why these four

They are the steps a research student repeats every week: read a paper, keep what matters, decide something, and make sure the references in a draft are real and say what the draft says they say. The skills insist on the same things a good supervisor would: page references, "not found" instead of a guess, and the decision left to the person.

## Install

From the Claude directory (Customize → plugins), or in Claude Code:

```
/plugin marketplace add najikay/claude-research-skills
/plugin install research-desk@claude-research-skills
```

## Tests and evals

- `python -m pytest -q` runs the server's offline tests (every HTTP call replaced by a fake); CI runs them on each push.
- `evals/` holds one case per skill (a prompt with a small inlined draft, bibliography or paper excerpt, and an LLM grader). `claude plugin eval . --runs 1` runs them; the citation and decision cases are ones a bare model fails without the plugin.

## Author

Naji Kayal, University of Haifa (robotics, SLAM, computer vision). Issues and suggestions are welcome here.

## License

Apache-2.0. See `LICENSE`.
