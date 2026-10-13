---
type: llm
weight: 1
---

This grader checks one thing: how the answer ends. The judge sees only the answer. For reference: the reply should end on one line that begins with "Next:" (bold or not, for example "**Next:**") and tells the user what to do or type next, for example "revise one of the three, paste the new version of that section and say *review this section again*".

PASS only if the last non-empty line of the answer begins with "Next:" (markdown bold or a leading bullet allowed). FAIL if there is no such line, or if other content (a table, a list, a question, a sign-off) comes after it.
