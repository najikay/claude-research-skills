---
name: decision-matrix
description: "Decide between named options with a weighted matrix: criteria and weights, a score with a reason per cell, what would flip the result, a recommendation and a reversible first step. Use when the user says \"help me decide between\", \"which should I choose?\" or \"X or Y?\" about concrete alternatives with real stakes: a method, a tool, a dataset, a design, a plan. Not for quick preferences, and not for a second opinion on one answer (use llm-council)."
---

# Decision matrix

1. **Frame**: one sentence for the decision, the deadline, and what is *not* being decided.
2. **Options**: 2–5 real alternatives, including "do nothing / defer" when that is honest.
3. **Criteria**: 3–6, each with a weight (1–5). Propose the weights from what the user said and carry on; say they can change any weight and you will rescore. Name the dealbreakers separately: they are not weights, and an option that hits one is out whatever its total.
4. **Score**: a table `option × criterion` with 1–5 scores and a one-phrase reason per cell; compute the weighted total and show the arithmetic once.
5. **Evidence**: for each score that decides the outcome, say where it comes from (what the user told you, a file, a link, a measurement). Mark guesses as guesses.
6. **Sensitivity**: which single weight or score flips the result? Say it plainly.
7. **Recommend**: the option, the reversible first step, and what would change the recommendation.

Do not decide for the user: the recommendation is yours, the decision is theirs.

## Where the result goes
Give the frame, the table, the sensitivity and the recommendation in the reply. Then a **decision record** in one block the user can keep: the decision in one line, the options, the weights, the totals, the recommendation, the reversible first step, `chosen:` left empty, and `revisit:` with a date only if the user gave one (otherwise `[when you will know more]`). When the user works in files and wants it kept, write that record as a note (frontmatter `type: decision`, `status: proposed`).

End with one line: **Next:** the reversible first step, as the thing to do today, then "when something changes, paste the record and say *rescore this*."
