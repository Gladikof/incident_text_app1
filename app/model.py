import json
from pathlib import Path

from joblib import load

# Шлях до папки з артефактами
ARTIFACTS = Path(__file__).resolve().parents[1] / "artifacts"


class Artifacts:
    """
    Обгортка для завантаження та використання моделей:
    - model_cat_text.joblib  (категорія)
    - model_pri_text.joblib  (пріоритет)
    - config.json            (поріг впевненості тощо)
    """

    def __init__(self):
        self.model_cat = None
        self.model_pri = None
        self.config = None

    def load_all(self):
        self.model_cat = load(ARTIFACTS / "model_cat_text.joblib")
        self.model_pri = load(ARTIFACTS / "model_pri_text.joblib")

        cfg_path = ARTIFACTS / "config.json"
        if cfg_path.exists():
            self.config = json.loads(cfg_path.read_text(encoding="utf-8"))
        else:
            self.config = {"confidence_threshold": 0.6}

    def cat_proba(self, X_df):
        """Ймовірності по категоріях."""
        proba = self.model_cat.predict_proba(X_df)[0]
        classes = list(self.model_cat.classes_)
        return dict(zip(classes, proba))

    def pri_proba(self, X_df):
        """Ймовірності по пріоритетах."""
        proba = self.model_pri.predict_proba(X_df)[0]
        classes = list(self.model_pri.classes_)
        return dict(zip(classes, proba))


ART = Artifacts()
