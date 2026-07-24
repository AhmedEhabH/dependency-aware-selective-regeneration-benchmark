from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np


@dataclass(frozen=True)
class EffectSize:
    name: str
    value: float
    magnitude: str
    interpretation: str = ""

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("EffectSize.name must not be empty")


class EffectSizeComputer:
    def __init__(self, method: Literal["cohen_d", "cliff_delta", "pooled_std"] = "cohen_d") -> None:
        self._method = method

    def cohens_d(self, group1: list[float], group2: list[float]) -> float:
        if not group1 or not group2:
            return 0.0

        n1, n2 = len(group1), len(group2)
        mean1, mean2 = float(np.mean(group1)), float(np.mean(group2))
        var1, var2 = float(np.var(group1, ddof=1)), float(np.var(group2, ddof=1))

        pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))

        if pooled_std == 0:
            return 0.0

        return float((mean1 - mean2) / pooled_std)

    def cliffs_delta(self, group1: list[float], group2: list[float]) -> float:
        if not group1 or not group2:
            return 0.0

        larger = 0
        smaller = 0
        equal = 0

        for x in group1:
            for y in group2:
                if x > y:
                    larger += 1
                elif x < y:
                    smaller += 1
                else:
                    equal += 1

        total = len(group1) * len(group2)
        return float((larger - smaller) / total)

    def pooled_std(self, group1: list[float], group2: list[float]) -> float:
        if not group1 or not group2:
            return 0.0

        n1, n2 = len(group1), len(group2)
        var1, var2 = float(np.var(group1, ddof=1)), float(np.var(group2, ddof=1))

        return float(np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)))

    def compute(
        self,
        group1: list[float],
        group2: list[float],
    ) -> EffectSize:
        if self._method == "cohen_d":
            value = self.cohens_d(group1, group2)
            magnitude = self._interpret_cohens_d(value)
            return EffectSize(
                name="cohen_d",
                value=value,
                magnitude=magnitude,
                interpretation=f"Cohen's d = {value:.4f} ({magnitude})",
            )
        elif self._method == "cliff_delta":
            value = self.cliffs_delta(group1, group2)
            magnitude = self._interpret_cliffs_delta(value)
            return EffectSize(
                name="cliff_delta",
                value=value,
                magnitude=magnitude,
                interpretation=f"Cliff's delta = {value:.4f} ({magnitude})",
            )
        else:
            return EffectSize(
                name="pooled_std",
                value=self.pooled_std(group1, group2),
                magnitude="N/A",
            )

    def _interpret_cohens_d(self, d: float) -> str:
        abs_d = abs(d)
        if abs_d < 0.2:
            return "negligible"
        elif abs_d < 0.5:
            return "small"
        elif abs_d < 0.8:
            return "medium"
        else:
            return "large"

    def _interpret_cliffs_delta(self, delta: float) -> str:
        abs_delta = abs(delta)
        if abs_delta < 0.147:
            return "negligible"
        elif abs_delta < 0.33:
            return "small"
        elif abs_delta < 0.474:
            return "medium"
        else:
            return "large"


def cohens_d(group1: list[float], group2: list[float]) -> float:
    if not group1 or not group2:
        return 0.0

    n1, n2 = len(group1), len(group2)
    mean1, mean2 = float(np.mean(group1)), float(np.mean(group2))
    var1, var2 = float(np.var(group1, ddof=1)), float(np.var(group2, ddof=1))

    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))

    if pooled_std == 0:
        return 0.0

    return float((mean1 - mean2) / pooled_std)


def cliffs_delta(group1: list[float], group2: list[float]) -> float:
    if not group1 or not group2:
        return 0.0

    larger = sum(1 for x in group1 for y in group2 if x > y)
    smaller = sum(1 for x in group1 for y in group2 if x < y)
    total = len(group1) * len(group2)

    return float((larger - smaller) / total)
