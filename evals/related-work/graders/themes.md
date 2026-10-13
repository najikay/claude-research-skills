---
type: llm
weight: 1
---

This grader checks one thing: the structure. The judge sees only the answer. For reference: the user's contribution is a radar-inertial odometry method that stays accurate in fog and smoke, where cameras and lidar degrade. The user asked for the classic systems to be mentioned, but supplied only four sources, to be cited with \cite: lin2023fastvo (a sparse monocular visual odometry front-end; 0.082 m ATE on EuRoC; fails under pure rotation and, per its Section 6, in low visibility); varga2022robustvo (stereo visual odometry that masks moving objects; evaluated on KITTI only, in clear weather); hale2021lidarfog (measures lidar range in artificial fog; usable range drops by about 60 % at 20 m visibility); ono2024radarodom (frame-to-frame radar odometry using Doppler; works in fog but drifts 2.1 % of distance travelled without an IMU).

PASS only if the sources are grouped into themes (for example camera odometry, lidar in poor visibility, radar odometry) with a paragraph each.
