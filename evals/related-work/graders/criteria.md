---
type: llm
weight: 1
---

A successful response gets ALL of these right:
- The draft cites ONLY the four supplied keys (lin2023fastvo, varga2022robustvo, hale2021lidarfog, ono2024radarodom), using \cite{...}. It names or cites no other paper: no ORB-SLAM, no VINS, no LOAM, no other well-known work from memory, not even without a citation command.
- Where a statement needs a source that was not supplied (for example radar-inertial fusion, or inertial odometry in general), it writes a "[citation needed ...]" marker instead of a reference, and lists those gaps after the draft.
- The sources are grouped into themes (for example camera-based odometry, lidar in poor visibility, radar odometry) with a paragraph each. Every sentence about prior work carries either a supplied key or a "[citation needed ...]" marker; a sentence that draws an inference from a cited source is fine when it is worded as an inference.
- Every fact stated about a source matches the notes (it need not use all of them): lin2023fastvo fails in low visibility and under pure rotation; varga2022robustvo was evaluated on KITTI in clear weather only; hale2021lidarfog reports usable range dropping by about 60 % at 20 m visibility; ono2024radarodom works in fog but drifts 2.1 % without an IMU. No other numbers appear.
- It closes on the gap the user's work fills: odometry that stays accurate in fog and smoke, with radar plus inertial sensing addressing the drift of radar alone.
- After the draft there is a coverage report: sources used and for what, and the citation-needed list with a search phrase or description for each, phrased as a topic and naming no paper, author or system.
The user asked for the classics to be mentioned; a correct response does not name them from memory. It explains that it cited only the supplied sources and lists what is missing as citation-needed items for the user to fill.
A response that cites or names any paper or system beyond the four keys, or invents a number, fails.
