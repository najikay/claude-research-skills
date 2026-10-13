---
type: llm
weight: 1
---

For reference, this was the whole text the user supplied (the judge sees only the answer):
- Title: Doppler-Aware Direct Radar Odometry. Authors: Cedric Le Gentil, Raphael Falque, Teresa Vidal-Calleja. 2025, arXiv.
- Abstract (p.1): "We present DRO, a direct radar odometry method that uses the Doppler velocity measured by a spinning FMCW radar to estimate ego-motion without extracting features. The method aligns consecutive radar scans directly in the signal domain and uses a gyroscope only for orientation."
- Results (p.6): "On the Boreas dataset, DRO reaches a translational drift of 1.6 % without a gyroscope and 0.9 % with one, against 2.3 % for the best feature-based baseline. Runtime is 40 ms per scan on a laptop CPU. The method fails on long straight highway sections where the Doppler profile is nearly symmetric (p.7)."
Quotes and details taken from this text are not invented. A "Keep:" and a "Next:" line after the note are expected.

A successful response is a note that:
- Has frontmatter with a citekey in the form firstauthorYYYYkeyword (e.g. `legentil2025doppler` or similar), the title, authors, year 2025, venue arXiv, and `status: draft`.
- Contains the sections: one-line takeaway, problem, method, evidence, limits, relevance, quotes (names may vary slightly but all seven ideas are present).
- Under evidence, reports the numbers exactly as given (1.6 %, 0.9 %, 2.3 %, 40 ms, Boreas) with page references (p.6), and under limits mentions the straight-highway failure (p.7).
- States that only the abstract and one results paragraph were available (does not pretend to have read the whole paper).
- Does not invent datasets, baselines, numbers or quotes beyond the given text.
