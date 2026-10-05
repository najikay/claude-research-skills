---
type: llm
weight: 1
---

This grader checks one thing: use of the one piece of source text. The judge sees only the answer. For reference: the only source text available was from [4] (He et al., Deep Residual Learning), page 6: "Our 152-layer residual net ... achieves 3.57% top-5 error on the ImageNet test set."

PASS only if the answer ties the 3.57 % top-5 figure to [4] and gives page 6 or the quote as its support. FAIL if the figure is called unverified, or if it is supported with a page or quote other than the one above.
