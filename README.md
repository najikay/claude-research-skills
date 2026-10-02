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
| `verify_reference` | one reference (title, authors, year, DOI, arXiv id) → `verified` (title, first author, year agree) / `partial` (title agrees; year off or no authors given) / `mismatch` (wrong author or title, or an identifier that points elsewhere) / `not_found` / `unchecked`, with the matched record and the reasons |
| `verify_bibtex` | the same for every entry of a `.bib` text, with counts |
| `lookup_reference` | clean metadata for a DOI, arXiv id or OpenAlex id |
| `search_works` | candidate papers for a few search words (OpenAlex searches titles, abstracts and full text) |
| `citation_neighbours` | what a paper cites and the most-cited papers citing it |

It asks two public, keyless services: [OpenAlex](https://openalex.org) (works by DOI or title) and [arXiv](https://arxiv.org) (arXiv ids), one request at a time, with arXiv's one-call-per-three-seconds rule respected. There is no account, key or storage.

**Data handling.** The server itself never sees your draft; Claude passes it a reference's title, DOI or arXiv id, or a few search words for `search_works`. Those go to `api.openalex.org` and `export.arxiv.org`, which see the request as any web request (your address, the plugin's user agent). Nothing is kept by the plugin. No personal data is read or stored. Author names in a bibliography are public bibliographic data and are sent only to match the paper.

**Platforms.** Python 3.10 or newer on the PATH as `python3` (on Windows, install Python from python.org and tick "Add to PATH"; if only `python` exists, change the command in `.mcp.json`).

## Why these four

They are the steps a research student repeats every week: read a paper, keep what matters, decide something, and make sure the references in a draft are real and say what the draft says they say. The skills insist on the same things a good supervisor would: page references, "not found" instead of a guess, and the decision left to the person.

## Install

From the Claude directory once the listing is live, or in Claude Code today:

```
/plugin marketplace add najikay/claude-research-skills
/plugin install research-desk@claude-research-skills
```

## Tests and evals

- `python -m pytest -q` runs the server's offline tests (every HTTP call replaced by a fake); CI runs them on each push.
- `evals/` holds one case per skill (a prompt with a small inlined draft, bibliography or paper excerpt, and an LLM grader). `claude plugin eval . --runs 1` runs them. On our runs every case scores 1.00 with the plugin, and the citation-check, decision-matrix and llm-council cases score 0.00 without it (the ablation column in the eval report); the evals exercise the skills, the server is covered by the unit tests.

## Author

Naji Kayal, University of Haifa (robotics, SLAM, computer vision). Issues and suggestions are welcome here.

## License

Apache-2.0. See `LICENSE`.

See `CHANGELOG.md` for versions.
