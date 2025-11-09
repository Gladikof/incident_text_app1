from pathlib import Path
from typing import Tuple

import joblib
from deep_translator import GoogleTranslator


class MLClassifier:
    """
    Обгортка над sklearn-пайплайном для прогнозу пріоритету інциденту.
    Використовує артефакт artifacts/model_pri_text.joblib
    (TF-IDF + LogisticRegression, навчений на англомовних тікетах).
    """

    def __init__(self):
        self.model = None
        base_dir = Path(__file__).resolve().parent.parent
        self.artifacts_dir = base_dir / "artifacts"
        self.model_path = self.artifacts_dir / "model_pri_text.joblib"

        # автопереклад у англійську
        self.translator = GoogleTranslator(source="auto", target="en")

    def load(self):
        if not self.model_path.exists():
            print(f"[ML] ⚠️ Файл моделі не знайдено: {self.model_path}")
            self.model = None
            return
        self.model = joblib.load(self.model_path)
        print(f"[ML] ✅ Модель пріоритету завантажено: {self.model_path}")

    def _to_english(self, text: str) -> str:
        """
        Переклад тексту в англійську. Якщо щось пішло не так – повертаємо оригінал.
        """
        text = (text or "").strip()
        if not text:
            return text
        try:
            translated = self.translator.translate(text)
            print(f"[ML] src->en: {text[:60]!r} -> {translated[:60]!r}")
            return translated
        except Exception as e:
            print(f"[ML] ⚠️ Не вдалося перекласти текст: {e}")
            return text  # fallback: без перекладу

    def predict_priority(self, text: str) -> Tuple[str, float]:
        """
        Повертає (label, confidence), де:
        - label: 'high' / 'medium' / 'low',
        - confidence: ймовірність цього класу (0..1).
        """
        if self.model is None:
            raise RuntimeError("ML модель не завантажена.")

        text_en = self._to_english(text)
        probs = self.model.predict_proba([text_en])[0]
        idx = probs.argmax()
        label = self.model.classes_[idx]
        conf = float(probs[idx])

        print(f"[ML] predict: {label} ({conf:.3f})")
        return label, conf


# Глобальний інстанс, щоб підняти один раз при старті
ml_model = MLClassifier()
