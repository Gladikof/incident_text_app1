from pathlib import Path
import re
import json

import pandas as pd
from datasets import load_dataset
from joblib import dump
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

# Папка, куди зберігаємо моделі та конфіг
ARTIFACTS = Path(__file__).resolve().parents[1] / "artifacts"
ARTIFACTS.mkdir(parents=True, exist_ok=True)


def normalize_text(s: str) -> str:
    """
    Нормалізація тексту: нижній регістр, видалення URL,
    залишаємо латиницю, кирилицю та цифри.
    """
    s = s.lower()
    s = re.sub(r"http\S+|www\S+", " ", s)
    s = re.sub(r"[^0-9a-zA-Zа-яА-ЯіїєґІЇЄҐ\s]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def load_hf_dataset() -> pd.DataFrame:
    """
    Завантаження датасету Tobi-Bueck/customer-support-tickets
    та приведення до формату:
        full_text, category, priority
    """
    # 1) Завантажуємо train-частину датасету
    ds = load_dataset("Tobi-Bueck/customer-support-tickets", split="train")
    df = ds.to_pandas()

    # 2) Беремо тільки англомовні тікети
    if "language" in df.columns:
        df = df[df["language"] == "en"].copy()

    # 3) Текст = subject + body
    subj = df["subject"] if "subject" in df.columns else ""
    body = df["body"] if "body" in df.columns else ""
    df["full_text"] = (
        subj.fillna("").astype(str) + " " + body.fillna("").astype(str)
    ).map(normalize_text)

    # 4) Категорія = queue (Technical Support, Billing and Payments, ...)
    if "queue" in df.columns:
        df["category"] = df["queue"].astype(str)
    else:
        df["category"] = "General"

    # 5) Пріоритет: беремо як є, викидаємо NaN і приводимо до рядків
    if "priority" in df.columns:
        df = df[~df["priority"].isna()].copy()
        df["priority"] = df["priority"].astype(str)
    else:
        df["priority"] = "1"

    # 6) Викидаємо порожній/дуже короткий текст
    df = df[df["full_text"].str.len() > 5].reset_index(drop=True)

    return df


def train_text_model(X, y, label: str, model_path: Path):
    """
    Універсальна функція тренування текстової моделі:
    TF-IDF + Logistic Regression.
    """
    pipe = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=(1, 2),
                    min_df=3,
                    max_features=50000,
                ),
            ),
            ("clf", LogisticRegression(max_iter=1000)),
        ]
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    pipe.fit(X_train, y_train)
    y_pred = pipe.predict(X_test)

    print(f"\n=== {label} MODEL ===")
    print(classification_report(y_test, y_pred, digits=3))

    dump(pipe, model_path)
    print(f"[+] Saved {label} model to {model_path}")


def main():
    df = load_hf_dataset()
    print(df[["full_text", "category", "priority"]].head())

    X = df["full_text"]

    # -------- Модель категорії --------
    y_cat = df["category"]
    train_text_model(
        X, y_cat, "CATEGORY", ARTIFACTS / "model_cat_text.joblib"
    )

    # -------- Модель пріоритету --------
    y_pri = df["priority"]
    train_text_model(
        X, y_pri, "PRIORITY", ARTIFACTS / "model_pri_text.joblib"
    )

    # -------- Конфіг --------
    cfg = {
        "confidence_threshold": 0.6,
    }
    (ARTIFACTS / "config.json").write_text(
        json.dumps(cfg, indent=2), encoding="utf-8"
    )
    print("[+] Saved config.json")


if __name__ == "__main__":
    main()
