---
name: paper-critique
description: "Review a draft the way a careful referee would: each claim checked against its evidence, missing baselines and controls, statistical weak points, threats to validity and clarity, ranked by severity with a concrete fix each. Use when the user asks \"review my paper\", \"what would reviewers say?\" or \"find the weaknesses\" in a paper, thesis chapter or report. Not for proofreading or rewriting, and not for checking that references are real (use citation-check)."
---

# Paper critique

Input: the user's draft, whole or in part. Say at the start what you were given and what you therefore cannot judge (a critique of an introduction cannot assess the experiments). If the paper is not the user's own (they are refereeing it, or reading it critically), give the same review addressed to its authors.

## Output, in this order
1. **How it reads**: three sentences on what the paper claims and why it should matter, as a reader would take it. If this differs from what the author intends, that is the first finding.
2. **Claims against evidence**: a table `claim · where it is made · evidence offered · verdict · fix`. Verdicts: `supported`, `partly` (say what is missing), `unsupported`, `overstated` (the evidence supports a weaker claim: give the weaker wording). Cover every claim in the abstract and the conclusion.
3. **Major issues**, ranked, each with the line it comes from and a concrete fix. Look for:
   - comparisons: a missing or weak baseline, an untuned baseline, a missing ablation for the component the paper credits;
   - statistics: one seed or one run, no variance, "significant" with no test, a difference smaller than the spread, results picked from the best run;
   - validity: the test data resembling the training data, a metric that does not measure the claim, conclusions beyond the setting tested;
   - reproducibility: a setting, a hyperparameter or a dataset split that a reader would need and cannot find.
4. **Minor issues**: clarity, undefined terms, figures that do not show what the text says, structure.
5. **Questions a reviewer will ask**, the five most likely.
6. **What is strong**, specifically: say which result or idea carries the paper, so the author protects it.
7. **If you change three things**: the three changes that most improve the paper's chances, in order.

## Rules
- Tie every finding to the line it concerns, quoted or pointed to. For something that is missing (an ablation, a baseline, a variance), point to the claim or section that needs it. A criticism tied to neither is cut.
- Be direct. No praise as padding, no softening a real problem.
- Do not rewrite the paper; show the fix in a sentence or an example line.
- Do not demand citations from memory. "A reader will expect a comparison with recent work on X" is fine; naming a specific paper is marked "from memory, check it exists".
- A fix must be something the author can do: an experiment, a control, a rewording, a cut.
