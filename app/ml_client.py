from __future__ import annotations

from typing import List, Tuple

from .ml_core import predict_priority_from_text

_PRIORITY_MAP = {
    "high": "P1",
    "medium": "P2",
    "low": "P3",
}


def predict_priority(
    *,
    text: str,
    department_name: str | None,
    department_criticality: str | None,
    asset_criticalities: List[str],
) -> Tuple[str, float]:
    """Wrapper that currently relies on text-only ML predictions."""
    priority, confidence = predict_priority_from_text(text)
    priority_label = _PRIORITY_MAP.get(priority, priority)
    return priority_label, confidence
