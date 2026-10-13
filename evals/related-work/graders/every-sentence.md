---
type: llm
weight: 1
---

This grader checks one thing: sourcing per sentence. The judge sees only the answer. For reference: the user's contribution is a radar-inertial odometry method that stays accurate in fog and smoke, where cameras and lidar degrade. The user asked for the classic systems to be mentioned, but supplied only four sources, to be cited with \cite: lin2023fastvo (a sparse monocular visual odometry front-end; 0.082 m ATE on EuRoC; fails under pure rotation and, per its Section 6, in low visibility); varga2022robustvo (stereo visual odometry that masks moving objects; evaluated on KITTI only, in clear weather); hale2021lidarfog (measures lidar range in artificial fog; usable range drops by about 60 % at 20 m visibility); ono2024radarodom (frame-to-frame radar odometry using Doppler; works in fog but drifts 2.1 % of distance travelled without an IMU).

PASS only if every sentence in the draft that states something about prior work carries a supplied key or a [citation needed] marker, or is worded as an inference from a cited source. General statements about the user's own method do not need one.
