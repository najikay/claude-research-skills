# Research Desk

Four skills for research work, as a Claude plugin. Each is plain instructions: nothing runs on your machine, and nothing leaves it beyond what you ask Claude to look up.

| skill | ask for it when | what you get |
|---|---|---|
| **citation-check** | before sharing a draft | a table per citation: resolvable, entry sane, supported by the source or `unverified`, style; orphans both ways; what to fix first; never an invented DOI, page or quote |
| **research-litnote** | you read a paper you will cite | a structured note (takeaway, problem, method, evidence with page refs, limits, relevance, quotes) with frontmatter and a citekey, left as a draft for you to accept |
| **decision-matrix** | you are choosing between alternatives | options × weighted criteria with evidence, a sensitivity check, a recommendation and a reversible first step; the decision stays yours |
| **llm-council** | a judgement call deserves more than one answer | several independent answers, then an anonymised judge: agreements, disagreements, claims to verify, a final answer with confidence |

## Why these four

They are the steps a research student repeats every week: read a paper, keep what matters, decide something, and make sure the references in a draft are real and say what the draft says they say. The skills insist on the same things a good supervisor would: page references, "not found" instead of a guess, and the decision left to the person.

## Install

From the Claude directory (Customize → plugins), or in Claude Code:

```
/plugin marketplace add najikay/claude-research-skills
/plugin install research-desk@claude-research-skills
```

## Evals

`evals/` holds one case per skill (a prompt with a small inlined draft, bibliography or paper excerpt, and an LLM grader). Run them with:

```
claude plugin eval . --runs 1
```

## Author

Naji Kayal, University of Haifa (robotics, SLAM, computer vision). Issues and suggestions are welcome here.

## License

Apache-2.0. See `LICENSE`.
