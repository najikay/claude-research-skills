---
type: llm
weight: 2
---

This grader checks that the answer reports what the lookup tools returned. The judge sees only the answer. For reference, the tools returned: [1] Attention Is All You Need: verified; [2] ORB-SLAM3: verified; [3] Fog Is No Obstacle: not found (its DOI does not resolve and no work has that title); [4] Deep Residual Learning: verified; [6] An Unused Reference: not found.

PASS only if ALL of these hold:
- The answer says near the top that it used the reference lookup tools (not web search, not memory).
- [1], [2] and [4] are reported as verified (found by the lookup).
- [3] is reported as not found and called suspect or likely invented, plainly.
- [6] is reported as not found, or as could not be confirmed. It is NOT called verified.
- No reference is given a status that contradicts the list above.
