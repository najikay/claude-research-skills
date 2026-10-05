---
type: llm
weight: 1
---

This grader checks one thing: the mismatches between the citations and the bibliography. The judge sees only the answer. For reference: the draft cites [1] to [5]; the bibliography has entries [1], [2], [3], [4] and [6].

PASS only if the answer reports BOTH: [5] is cited in the draft but has no bibliography entry, and [6] is a bibliography entry that the draft never cites. Any clear wording counts ("orphan", "missing", "not cited", "unused").
