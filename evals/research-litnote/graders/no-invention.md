---
type: llm
weight: 1
---

This grader checks one thing: invention. The judge sees only the answer. For reference, the whole text the user supplied: Title: Doppler-Aware Direct Radar Odometry. Authors: Cedric Le Gentil, Raphael Falque, Teresa Vidal-Calleja. 2025, arXiv. Abstract (p.1): "We present DRO, a direct radar odometry method that uses the Doppler velocity measured by a spinning FMCW radar to estimate ego-motion without extracting features. The method aligns consecutive radar scans directly in the signal domain and uses a gyroscope only for orientation." Results (p.6): "On the Boreas dataset, DRO reaches a translational drift of 1.6 % without a gyroscope and 0.9 % with one, against 2.3 % for the best feature-based baseline. Runtime is 40 ms per scan on a laptop CPU. The method fails on long straight highway sections where the Doppler profile is nearly symmetric (p.7)." The user asked for nothing to be saved to disk.

PASS only if the note adds no dataset, baseline, number or quote beyond the supplied text above. Quoting or paraphrasing the supplied text is fine; the note's own judgement marked as such is fine.
