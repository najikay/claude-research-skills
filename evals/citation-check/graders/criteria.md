---
type: llm
weight: 1
---

A successful response gets ALL of these right:
- `[5]` is a citation with no bibliography entry, and `[6]` is an entry never cited: both are reported as orphans (one each way).
- The 3.57 % claim: the sentence attributes it to [5] but the quoted source text is from [4]; the response notices the number is supported by [4]'s page 6 and that [5] is wrong/missing, rather than marking [5] supported.
- The "1 cm accuracy on every EuRoC sequence" claim is marked `unverified` (or "cannot be checked here"), NOT `supported`, because no source text was given for [2].
- `[3]` is flagged as suspect or likely invented (implausible title/venue, a DOI prefix that does not look real), and marked `unchecked`/`not verified` rather than real, since no lookup tools were available.
- The results come as a per-citation table with columns for resolvable/real, support and style (names may vary), followed by a "fix first" list that puts the orphans and the suspect reference before style issues.
- `[1]` and `[4]` are well-known papers, but no lookup was possible: they are reported as `unchecked` (or "recognised, unchecked" / "could not be looked up here"), NOT as `verified` or confirmed real. The response says near the top that no lookup tools or web search were used.
- No DOI, page number or quote is invented anywhere.
A response that marks [2] or [5] as supported, that treats [3] as verified, or that calls [1] or [4] verified from memory, fails.
