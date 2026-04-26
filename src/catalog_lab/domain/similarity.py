from __future__ import annotations

from typing import List, Sequence, Tuple

import numpy as np


def top_k_indices(
    scores: np.ndarray, k: int, exclude: Sequence[int] | None = None
) -> List[Tuple[int, float]]:
    scores = np.asarray(scores, dtype=np.float64)
    exclude_set = set(exclude or [])
    order = np.argsort(-scores)
    out: List[Tuple[int, float]] = []
    for idx in order:
        if int(idx) in exclude_set:
            continue
        out.append((int(idx), float(scores[idx])))
        if len(out) >= k:
            break
    return out
