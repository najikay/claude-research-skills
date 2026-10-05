---
name: llm-council
description: "Get several independent opinions on a hard question and a judged synthesis: answers from different viewpoints, where they agree and disagree, what must be verified, and a final answer with a confidence. Use when the user asks for \"a second opinion\", \"sanity-check this\", \"argue both sides\", \"am I missing something?\", or faces a high-stakes judgement call or design review. Not for factual lookups or routine questions."
---

# LLM council

A council is `N` independent answers plus one judge. Independence matters more than the size of any one model. Three seats is a good default.

## Procedure
1. Write the question once, with the context needed to answer it and the format wanted (bullets, table, decision). This is the prompt every seat gets.
2. Seat the council by what you have:
   - **One model, one conversation** (the usual case): answer the prompt three times, each from a different stance held all the way through: a sceptic who looks for what breaks, a domain expert who cares about correctness, and the person who has to live with the result. Write each answer in full before starting the next, and do not let a later seat revise an earlier one.
   - **Sub-agents or other models you can reach**: give each the same prompt in a fresh context, without showing it the others.
3. Judge: take the answers *anonymised* (A, B, C) and report: agreements, disagreements with the strongest argument on each side, factual claims to verify, and a final answer with a confidence of 0–1.
4. Report: the synthesis first, then a short table `seat · position · confidence`. Name which points still need a human.

## Rules
- Say which kind of council this was. Three stances of one model share that model's blind spots: the report says so, and treats their agreement as weaker than agreement between different models.
- Two seats agreeing is not evidence; a verifiable claim is. Verify what can be verified before the synthesis, and mark what could not be.
- Do not send confidential material to a seat the user has not approved for it.
- Keep the seats' full answers available on request; the synthesis never replaces them.
