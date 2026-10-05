---
type: llm
weight: 1
---

A successful response gets ALL of these right:
- It opens with a short statement of how the paper reads to a reader.
- It then checks the claims against the evidence in a table, one row per claim, covering the claims of the abstract and the conclusion, each row with where the claim is made, the evidence offered, a verdict (words such as supported / partly / unsupported / overstated; the exact label does not matter) and a fix. For at least one claim that overreaches, whatever label it was given, it offers the weaker wording the evidence does support.
- "Significantly outperforms" / "significantly better" is flagged: one run with one seed, no variance, no statistical test, and a difference of 0.05 m (0.42 against 0.47) that may be within the spread. The fix asks for several seeds with mean and spread or a test.
- "All existing methods" and "state of the art" are flagged as unsupported or overstated: only one baseline (a potential field) was compared, and it used default, untuned parameters.
- "Runs in real time on embedded hardware" is flagged as unsupported: no timing numbers and no hardware are reported.
- The claim that the collision-avoidance module (CAM) is the key is flagged: there is no ablation removing CAM.
- "Will work in real outdoor deployments" is flagged as going beyond the evidence: one simulated arena with 12 drones.
- The findings are ranked (major before minor), each tied to the draft's own words, each with a concrete fix the author can do.
- It lists the questions a reviewer is most likely to ask (about five), says specifically what is strong or worth protecting in the paper rather than offering general praise, and ends with exactly three changes that would most improve the paper, in order.
- It does not invent results, and any specific paper it names as a missing comparison is marked as from memory or to be checked.
A response that mainly praises the draft, or that misses the single-seed problem or the missing ablation, fails.
