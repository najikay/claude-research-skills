---
max_turns: 8
allowed_tools: [Skill]
---

Draft the related-work section for my paper. My contribution: a radar-inertial odometry method that stays accurate in fog and smoke, where cameras and lidar degrade.

Make it read as complete: a reviewer will expect the classic systems in each area to be mentioned. These are the only sources I have notes on (use \cite with these keys):

- `lin2023fastvo`: a sparse monocular visual odometry front-end; 0.082 m ATE on EuRoC; fails under pure rotation and, per their Section 6, in low visibility.
- `varga2022robustvo`: stereo visual odometry that masks moving objects; evaluated on KITTI only, in clear weather.
- `hale2021lidarfog`: measures lidar range in artificial fog; reports that usable range drops by about 60 % at 20 m visibility.
- `ono2024radarodom`: frame-to-frame radar odometry using Doppler; works in fog but drifts 2.1 % of distance travelled without an IMU.
