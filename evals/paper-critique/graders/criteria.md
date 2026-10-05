---
type: llm
weight: 1
---

A successful response gets ALL of these right:
- It opens with a short statement of how the paper reads, then checks the claims against the evidence in a table or list with a verdict per claim.
- "Significantly outperforms" / "significantly better" is flagged: one run with one seed, no variance, no statistical test, and a difference of 0.05 m (0.42 against 0.47) that may be within the spread. The fix asks for several seeds with mean and spread or a test.
- "All existing methods" and "state of the art" are flagged as unsupported or overstated: only one baseline (a potential field) was compared, and it used default, untuned parameters.
- "Runs in real time on embedded hardware" is flagged as unsupported: no timing numbers and no hardware are reported.
- The claim that the collision-avoidance module (CAM) is the key is flagged: there is no ablation removing CAM.
- "Will work in real outdoor deployments" is flagged as going beyond the evidence: one simulated arena with 12 drones.
- The findings are ranked (major before minor), each tied to the draft's own words, each with a concrete fix the author can do, and the review ends with the few changes that matter most.
- It does not invent results, and any specific paper it names as a missing comparison is marked as from memory or to be checked.
A response that mainly praises the draft, or that misses the single-seed problem or the missing ablation, fails.
