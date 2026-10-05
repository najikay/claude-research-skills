---
name: related-work
description: "Draft a related-work or literature-review section from sources the user supplies, grouped by theme, every sentence tied to its source, ending on the gap the user's work fills, with a list of claims that still need a citation. Use when the user asks \"write my related work\", \"draft the literature review\" or \"position my paper against these\" and provides notes, PDFs or a bibliography. Not for finding papers on a topic, and never as a source of citations the user did not provide."
---

# Related work

Input: (a) what the user's own work does, in a sentence or two; (b) the sources: literature notes, PDFs, abstracts, or a bibliography with enough text to know what each paper shows. Ask for (a) if it is missing: a related-work section argues toward a gap, and you need to know which one.

## The one rule
**Cite only what the user supplied.** A sentence about prior work carries the key of a supplied source that actually says it. If a sentence needs a source you were not given, write `[citation needed: <what kind of paper>]` in its place. Never fill the gap from memory, however well known the paper.

## Steps
1. **Inventory**: list the sources with one line each on what it shows and the basis (full text, abstract, note). A source too thin to cite safely (a title alone) is listed as "need more to use".
2. **Themes**: group the sources into two to four lines of work that lead toward the user's contribution. A source can serve two themes; a theme with one source is fine if it matters.
3. **Draft**, one paragraph per theme: what this line of work set out to do, what the key sources showed (each with its key), and the limitation that matters for the user's work. Then a closing paragraph that states the gap and how the user's work addresses it.
4. **Coverage report**, after the draft:
   - sources used, and for what;
   - sources not used, and why;
   - every `[citation needed]` with a search phrase that would find a candidate;
   - claims in the draft that rest on an abstract only.

## Style
- The citation form follows the sources: `\cite{key}` when the user gave BibTeX keys, (Author, year) or [n] otherwise.
- Prior work is described fairly, in terms its authors would accept. The gap is a limitation, not a failing.
- Results are stated with their conditions (dataset, setting). No number that is not in the supplied material.
- Length: about 150 words per theme unless the user says otherwise.

## With lookup tools or web search
You may look for candidates to fill a `[citation needed]`, and list them **after** the draft under "candidates to check", with why each might fit. They enter the text only when the user accepts them.
