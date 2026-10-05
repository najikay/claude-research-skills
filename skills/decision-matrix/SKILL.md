---
name: decision-matrix
description: "Decide between named options with a weighted matrix: criteria and weights, a score with a reason per cell, what would flip the result, a recommendation and a reversible first step. Use when the user says \"help me decide between\", \"which should I choose?\" or \"X or Y?\" about concrete alternatives with real stakes: a purchase, a job offer, a design, a plan. Not for quick preferences, and not for questions with one obvious answer."
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
Give the frame, the table, the sensitivity and the recommendation in the reply. Only when the user is working in files and wants it kept, also write it as a note (frontmatter `type: decision`, `status: proposed`, `options`, `chosen` left empty until the user decides).
