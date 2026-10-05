---
name: paper-compare
description: "Compare two to five papers side by side: problem, method, data, headline results, assumptions and limits, then what each one adds, where they cannot be compared, and which to cite for what. Use when the user shares several papers and asks \"compare these papers\", \"how do these differ?\", \"which approach is better?\" or is choosing a baseline. Not for a single paper (use research-litnote), and not for writing a related-work section (use related-work)."
---

# Paper comparison

Input: two to five papers, as PDFs, links, the user's notes, or pasted text. With more than five, ask which matter most or compare in groups.

## Steps
1. **State the basis** for each paper in one line: full text, abstract only, or the user's note. A row filled from an abstract is marked so. If you cannot get a paper's text at all (a link you cannot open, a title only), say so and ask for the text or the PDF; that paper's column stays empty with `basis: none`. Never fill a column from what you remember about a paper.
2. **Fix the question**: what is the user comparing them *for* (choosing a method, picking a baseline, writing a survey)? If they did not say, assume "which should I build on or cite" and say that you assumed it.
3. **Build the table**, one column per paper, these rows: problem addressed · core idea · what is new · data or setup · headline result (the number, its metric, its dataset, and where it stands: the page if the text shows one, else the section or table) · assumptions · stated limits · code or data available.
4. **Comparability**: before any ranking, check that the results share a dataset, a metric and a protocol. Where they do not, say "not directly comparable" and why. Never rank accuracy across different benchmarks. You may still recommend one for the user's purpose on other stated grounds (sensor, hardware, speed, available code, assumptions), saying that this is what the recommendation rests on.
5. **Reading**, four short parts:
   - *What each one adds* (one line each).
   - *Where they agree and where they conflict* (conflicts with both places cited).
   - *Which to cite for what* (this claim → that paper).
   - *What none of them answers.*

## Rules
- Numbers are copied, not rounded, with where they stand in the paper. Never estimate a page number. "Not stated" is an answer; so is "not in the part I read".
- A paper's own claim about itself is reported as its claim ("the authors report"), not as established fact.
- No verdict of "better" without a shared benchmark, or without saying on what the judgement rests.
- Do not bring in papers the user did not supply. You may list, separately and marked as suggestions, what else they might compare against: found with lookup tools or web search and given with a link, or else marked "from memory, check it exists".

## Where the result goes
In the reply: the table, then the reading. Write a file only when the user works in files and asks for it.
