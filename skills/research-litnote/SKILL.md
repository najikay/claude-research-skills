---
name: research-litnote
description: "Turn a paper into a structured literature note: one-line takeaway, problem, method, evidence with page references, limits, and quotes worth keeping. Use when the user shares a paper (a PDF, an arXiv link, pasted text) and says \"summarise this paper\", \"make notes on this\", \"what does this paper claim?\", or will cite it later. Not for a one-sentence answer about a paper, and not for comparing several papers (use paper-compare)."
---

# Literature note

One note per paper, named by citekey (`firstauthorYYYYkeyword`, lowercase).

## Where the note goes
- **You can write files and the user keeps notes in a folder**: save it there by citekey (ask once where; a `lit/` folder is a good default). Never overwrite an existing note: append a dated section instead.
- **Otherwise** (a chat with no files): give the whole note in the reply as one fenced block the user can copy. Do not ask where to save it.

## Steps
1. Get the text: read the PDF, open the arXiv abstract page, or use the text the user pasted. Say at the top of the note when you only had the abstract or a part of the paper; a note from an abstract is marked `basis: abstract only`.
2. Fill the template below. Every claim under *Evidence* carries a page or section reference; numbers are copied, not rounded.
3. Link: mention related notes the user already has when you can see them.
4. Leave the note marked `status: draft`. The user reviews it; do not mark it reviewed yourself.

## Template
```
---
type: lit
citekey: <citekey>
title: <title>
authors: [..]
year: <yyyy>
venue: <venue or arXiv>
tags: [..]
basis: full text | abstract only | sections <which>
status: draft
created: <yyyy-mm-dd>
---
## One-line takeaway
## Problem and why it matters
## Method (what is new)
## Evidence (datasets, baselines, numbers, page refs)
## Limits and open questions
## Relevance to your work
## Quotes worth keeping (with page)
```

## Rules
- A note is faithful to the paper: the paper's claims in the paper's words, with the page. Your own judgement goes only under *Limits* and *Relevance*, marked as yours.
- When the paper contradicts itself (abstract against body), say so and cite both places.
- No invented numbers, datasets or baselines; "not stated" is an answer. What the text you had does not cover is "not in the part I read", not a guess.
