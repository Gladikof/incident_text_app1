import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
from pathlib import Path

DATA_PATH = Path("training/data/incidents.csv")
ARTIFACT_PATH = Path("app/models/ml_priority.joblib")

df = pd.read_csv(DATA_PATH)
X_train, X_test, y_train, y_test = train_test_split(df["text"], df["priority"], test_size=0.2, random_state=42)

# TF-IDF + Logistic Regression pipeline
pipe = Pipeline([
    ("tfidf", TfidfVectorizer(max_features=2000, ngram_range=(1,2))),
    ("clf", LogisticRegression(max_iter=1000))
])

pipe.fit(X_train, y_train)
preds = pipe.predict(X_test)

print(classification_report(y_test, preds))
joblib.dump(pipe, ARTIFACT_PATH)
print(f"[+] Saved ML model to {ARTIFACT_PATH}")
