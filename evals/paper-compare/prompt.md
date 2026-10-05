---
max_turns: 8
allowed_tools: [Skill]
---

Compare these three papers for me. I need to pick one as the baseline for my own visual odometry work. All I have of each is the text below.

**Paper A** — "FastVO: Lightweight Monocular Odometry" (Lin et al., 2023). Abstract: we propose a sparse monocular VO front-end for embedded boards. Section 5, Table 2: on the EuRoC MAV dataset (MH_01 to MH_05) the absolute trajectory error (ATE RMSE) is 0.082 m on average; runs at 120 Hz on a Jetson Nano. Limitation stated in Section 6: fails under pure rotation.

**Paper B** — "DeepTrack: Learned Dense Visual Odometry" (Okafor and Marsh, 2024). Abstract only: a dense learned VO that "substantially outperforms classical methods". No numbers in the abstract.

**Paper C** — "RobustVO: Odometry in Dynamic Scenes" (Varga et al., 2022). Section 4.2, Table 1: on KITTI odometry sequences 00 to 10 the translational error is 1.12 %; 25 Hz on a desktop GPU. Section 3 assumes a stereo camera.
