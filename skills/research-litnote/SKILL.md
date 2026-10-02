---
name: research-litnote
description: Turn a paper (PDF, arXiv id or URL) into a structured literature note with citation, claims, method, evidence with page references, limits and links. Use when the user reads, saves or asks for a summary of a paper they will cite later.
---

# Literature note

One note per paper, named by citekey (`firstauthorYYYYkeyword`, lowercase), saved where the user keeps notes (ask once; a `lit/` folder is a good default). Never overwrite an existing note: append a dated section instead.

## Steps
1. Get the text: read the PDF, fetch the arXiv abstract page, or use the text the user pasted. Say when you only had the abstract.
2. Fill the template below. Every claim under *Evidence* carries a page or section reference; numbers are copied, not rounded.
3. Link: mention related notes the user already has when you can see them; add the citekey to the user's reading log if they keep one.
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
- When the paper contradicts itself (abstract vs body), say so and cite both places.
- No invented numbers, datasets or baselines; "not stated" is an answer.
