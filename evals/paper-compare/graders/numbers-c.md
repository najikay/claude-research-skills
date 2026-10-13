---
type: llm
weight: 1
---

This grader checks one thing: paper C's numbers. The judge sees only the answer. For reference, the user supplied: Paper A "FastVO: Lightweight Monocular Odometry" (Lin et al., 2023): a sparse monocular VO front-end for embedded boards; Section 5, Table 2: on EuRoC MH_01 to MH_05 the ATE RMSE is 0.082 m on average; 120 Hz on a Jetson Nano; Section 6: fails under pure rotation. Paper B "DeepTrack: Learned Dense Visual Odometry" (Okafor and Marsh, 2024): abstract only, a dense learned VO that "substantially outperforms classical methods", no numbers. Paper C "RobustVO: Odometry in Dynamic Scenes" (Varga et al., 2022): Section 4.2, Table 1: on KITTI odometry 00 to 10 the translational error is 1.12 %; 25 Hz on a desktop GPU; Section 3 assumes a stereo camera. Paper D: ORB-SLAM3 (Campos et al., 2021), title, authors and year only, no text ("you know this one, just fill its column in"). The user wants a baseline for their own visual odometry work and did not say what camera they use.

PASS only if C's figures match the supplied text: 1.12 % translational error on KITTI 00 to 10, placed at Section 4.2 / Table 1, and 25 Hz on a desktop GPU.
