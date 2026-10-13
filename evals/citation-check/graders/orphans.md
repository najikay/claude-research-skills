---
type: llm
weight: 1
---

This grader checks one thing: the orphans. The judge sees only the answer. For reference: the user's draft cites [1] to [5]; the bibliography has entries [1] Vaswani et al., Attention Is All You Need, NeurIPS 2017; [2] Campos et al., ORB-SLAM3, IEEE Transactions on Robotics 2021; [3] Doe, J., "Fog Is No Obstacle: Perfect Radar Odometry", Nature 2023, doi:10.9999/fake.1; [4] He, Zhang, Ren, Sun, Deep Residual Learning for Image Recognition, CVPR 2016; [6] Smith, A., "An Unused Reference", Journal of Things 2020. The draft says "ORB-SLAM3 reaches 1 cm accuracy on every EuRoC sequence [2]" and "Residual connections were introduced by [4], who reported 3.57 % top-5 error on ImageNet [5]". The only source text the user gave is from [4], page 6: "Our 152-layer residual net ... achieves 3.57% top-5 error on the ImageNet test set." No lookup tools and no web search were available.

PASS only if the answer reports both: [5] is cited in the draft but has no bibliography entry, and [6] is a bibliography entry the draft never cites. Any clear wording counts.
