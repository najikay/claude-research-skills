---
type: llm
weight: 1
---

This grader checks one thing: that a reference being real is not treated as proof of the sentence that cites it. The judge sees only the answer. For reference: the lookup found [2] (ORB-SLAM3) to be a real paper, and no text from that paper was available. The draft's sentence was "ORB-SLAM3 reaches 1 cm accuracy on every EuRoC sequence [2]".

PASS only if the answer treats the claim "1 cm accuracy on every EuRoC sequence" as NOT confirmed (for example "unverified", "could not check", "no source text", "risky"), even though the reference itself is reported as real. FAIL if the answer calls that claim supported or correct.
