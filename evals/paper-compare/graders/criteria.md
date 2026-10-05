---
type: llm
weight: 1
---

A successful response gets ALL of these right:
- It states the basis for each paper: A and C from sections of the paper, B from the abstract only, and it treats B's "substantially outperforms" as the authors' claim with no number to check ("not stated"), not as a result.
- It gives a side-by-side table with one column per paper and rows covering at least problem or idea, data or setup, headline result and limits or assumptions.
- The numbers are copied exactly with where they stand: 0.082 m ATE RMSE on EuRoC MH_01 to MH_05 (Section 5, Table 2) and 120 Hz on a Jetson Nano for A; 1.12 % translational error on KITTI 00 to 10 (Section 4.2, Table 1) and 25 Hz on a desktop GPU for C. No number is invented for B.
- It says A and C are NOT directly comparable, because they use different datasets and different metrics (ATE in metres on EuRoC against percent translational error on KITTI), and it does not rank them by accuracy.
- It notes the points that matter for the user's choice: C assumes a stereo camera while the user's work and A are monocular or the camera type is flagged as a deciding question, and A fails under pure rotation.
- It ends with what each adds or which to cite or build on for what, and what is still unknown (B's actual results).
A response that declares one paper more accurate than another across the two datasets, or that fills in a result for B, fails.
