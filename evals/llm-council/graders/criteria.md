---
type: llm
weight: 1
---

A successful response:
- Produces at least three clearly separated independent answers (seats) with different framings, each answering the question on its own without referring to the others.
- Then a judge section that anonymises the seats (A, B, C...), lists agreements, disagreements with the strongest argument on each side, claims that would need verification, and a final answer with a numeric confidence between 0 and 1.
- Ends with a short table of seat · position · confidence, and names what still needs a human decision.
- Does not treat agreement between seats as proof.
- It says that the seats are stances of one model (not different models) and that their agreement is therefore weaker evidence.
