from pathlib import Path
from typing import Tuple

import joblib
from deep_translator import GoogleTranslator


class MLClassifier:
    """Wrapper around sklearn text classifiers for priority and category."""

    def __init__(self):
        self.model = None
        self.version = "unknown"
        self.vectorizer = None
        self.category_model = None
        self.category_version = "unknown"
        self.category_vectorizer = None
        base_dir = Path(__file__).resolve().parent.parent
        self.artifacts_dir = base_dir / "artifacts"
        self.model_path = self.artifacts_dir / "model_pri_text.joblib"
        self.category_model_path = self.artifacts_dir / "model_cat_text.joblib"
        self.translator = GoogleTranslator(source="auto", target="en")

    def load(self):
        if not self.model_path.exists():
            print(f"[ML] WARNING: model artifact not found: {self.model_path}")
            self.model = None
            return

        priority_payload = joblib.load(self.model_path)
        self.version = self.model_path.stem
        if isinstance(priority_payload, dict) and "model" in priority_payload:
            self.model = priority_payload["model"]
            self.vectorizer = priority_payload.get("vectorizer")
        else:
            self.model = priority_payload
            self.vectorizer = None
        print(f"[ML] SUCCESS: priority model loaded: {self.model_path}")

        if self.category_model_path.exists():
            category_payload = joblib.load(self.category_model_path)
            self.category_version = self.category_model_path.stem
            if isinstance(category_payload, dict) and "model" in category_payload:
                self.category_model = category_payload["model"]
                self.category_vectorizer = category_payload.get("vectorizer")
            else:
                self.category_model = category_payload
                self.category_vectorizer = None
            print(f"[ML] SUCCESS: category model loaded: {self.category_model_path}")
        else:
            self.category_model = None
            self.category_vectorizer = None

    def _to_english(self, text: str) -> str:
        text = (text or "").strip()
        if not text:
            return text
        try:
            translated = self.translator.translate(text)
            return translated
        except Exception as exc:  # pragma: no cover
            print(f"[ML] WARNING: translation failed: {exc}")
            return text

    def _vectorize(self, text: str, vectorizer):
        inputs = [text]
        if vectorizer is not None:
            return vectorizer.transform(inputs)
        return inputs

    def predict_priority(self, text: str) -> Tuple[str, float]:
        if self.model is None:
            raise RuntimeError("Priority ML model is not loaded.")

        text_en = self._to_english(text)
        probs = self.model.predict_proba(self._vectorize(text_en, self.vectorizer))[0]
        idx = probs.argmax()
        label = self.model.classes_[idx]
        conf = float(probs[idx])
        return label, conf

    def predict_category(self, text: str) -> Tuple[str, float]:
        if self.category_model is None:
            raise RuntimeError("Category ML model is not loaded.")

        text_en = self._to_english(text)
        probs = self.category_model.predict_proba(
            self._vectorize(text_en, self.category_vectorizer)
        )[0]
        idx = probs.argmax()
        label = self.category_model.classes_[idx]
        conf = float(probs[idx])
        return label, conf


ml_model = MLClassifier()
