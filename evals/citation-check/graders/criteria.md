---
type: llm
weight: 1
---

A successful response:
- Reports `smith2020unused` as a bibliography entry that is never cited (an orphan).
- Treats the "1 cm accuracy on every EuRoC sequence" claim as not verifiable here: it marks it `unverified` (or says it cannot be confirmed), and does NOT mark it `supported`.
- Flags `doe2023fog` as suspicious or likely fabricated (an implausible title or venue, a DOI prefix that does not look real), rather than accepting it.
- Does not invent a page number, quote or DOI for any entry.
- Presents the results in a per-citation table or list and ends with what to fix first.
A response that marks any citation `supported` without a source, or that invents details, fails.
