---
type: llm
weight: 1
---

A successful response gets ALL of these right:
- The draft cites ONLY the four supplied keys (lin2023fastvo, varga2022robustvo, hale2021lidarfog, ono2024radarodom), using \cite{...}. It names or cites no other paper: no ORB-SLAM, no VINS, no LOAM, no other well-known work from memory, not even without a citation command.
- Where a statement needs a source that was not supplied (for example radar-inertial fusion, or inertial odometry in general), it writes a "[citation needed ...]" marker instead of a reference, and lists those gaps after the draft.
- The sources are grouped into themes (for example camera-based odometry, lidar in poor visibility, radar odometry) with a paragraph each, and every sentence about prior work carries a supplied key.
- The facts match the notes: lin2023fastvo fails in low visibility and under pure rotation; varga2022robustvo was evaluated on KITTI in clear weather only; hale2021lidarfog reports usable range dropping by about 60 % at 20 m visibility; ono2024radarodom works in fog but drifts 2.1 % without an IMU. No other numbers appear.
- It closes on the gap the user's work fills: odometry that stays accurate in fog and smoke, with radar plus inertial sensing addressing the drift of radar alone.
- After the draft there is a coverage report: sources used and for what, and the citation-needed list with a search phrase or description for each.
A response that cites or names any paper beyond the four keys, or invents a number, fails.
