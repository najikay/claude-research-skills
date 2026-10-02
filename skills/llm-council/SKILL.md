---
name: llm-council
description: Get several independent answers to a question, then a judged synthesis. Use for high-stakes judgement calls, design reviews, or when one answer feels unreliable and the user wants it checked rather than repeated.
---

# LLM council

A council is `N` independent answers plus one judge. Independence matters more than the size of any one model.

## Procedure
1. Write the question once, with the context needed to answer it and the format wanted (bullets, table, decision). Save it as the prompt.
2. Get each seat's answer to the same prompt *without* showing it the others. Seats can be: different models you can reach, the same model in fresh contexts with different framings (sceptic, domain expert, end user), or sub-agents when you can run them. Three seats is a good default.
3. Judge: give one seat all answers *anonymised* (A, B, C) and ask for: agreements, disagreements with the strongest argument on each side, factual claims to verify, and a final answer with a confidence of 0–1.
4. Report: the synthesis, then a short table `seat · position · confidence`. Name which points still need a human.

## Rules
- Do not send confidential material to a seat the user has not approved for it.
- Two seats agreeing is not evidence; a verifiable claim is. Verify what can be verified before the synthesis.
- Keep the seats' raw answers available on request; the synthesis never replaces them.
