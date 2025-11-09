from __future__ import annotations

from typing import Tuple

from .ml_model import ml_model


def predict_priority_from_text(text: str) -> Tuple[str, float]:
    """Proxy that ensures the global ML model is used consistently."""
    if ml_model.model is None:
        raise RuntimeError("ML model is not loaded")
    return ml_model.predict_priority(text)
