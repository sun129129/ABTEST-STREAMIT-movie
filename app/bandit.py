import numpy as np
from collections import defaultdict
from typing import Dict, List, Tuple

class ThompsonBandit:
    def __init__(self, arms: List[str], discount: float = 1.0):
        self.arms = arms
        self.a = defaultdict(lambda: 1.0)  # successes
        self.b = defaultdict(lambda: 1.0)  # failures
        self.n = defaultdict(int)          # exposures
        self.discount = discount

    def choose(self) -> Tuple[str, Dict[str, float]]:
        samples = {arm: np.random.beta(self.a[arm], self.b[arm]) for arm in self.arms}
        arm = max(samples, key=samples.get)
        self.n[arm] += 1
        return arm, samples

    def update(self, arm: str, reward: float):
        # 감쇠 적용(최근성 반영)
        if self.discount < 1.0:
            for k in self.arms:
                self.a[k] *= self.discount
                self.b[k] *= self.discount
        self.a[arm] += reward
        self.b[arm] += (1 - reward)

    # 유틸
    def ctr(self, arm: str) -> float:
        denom = self.a[arm] + self.b[arm]
        return self.a[arm] / denom if denom > 0 else 0.0
