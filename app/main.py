from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from .schemas import IncidentIn, LLMIncidentOut
from .llm_router import route_with_llm
from .ml_model import ml_model

# === Шляхи ===
# __file__ -> ...\incident_text_app\app\main.py
# BASE_DIR  -> ...\incident_text_app
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

print(f"[DEBUG] FRONTEND_DIR = {FRONTEND_DIR}  exists={FRONTEND_DIR.exists()}")

app = FastAPI(
    title="Service Desk LLM Router",
    version="1.0.0",
    description=(
        "Прототип сервіс-деск системи для автоматизованої класифікації та "
        "пріоритизації інцидентів із застосуванням LLM."
    ),
)


@app.on_event("startup")
def _load_ml():
    """
    Завантаження ML-моделі при старті бекенду.
    """
    try:
        ml_model.load()
    except Exception as e:
        print("[ML] ❌ Не вдалося завантажити модель:", e)


# === API ===


@app.post("/classify_llm", response_model=LLMIncidentOut)
def classify_llm(inc: IncidentIn):
    """
    Гібридна маршрутизація інциденту:
    - LLM (через Ollama) повертає категорію, пріоритет, терміновість, команду, виконавця;
    - ML-модель тексту окремо оцінює пріоритет і додає ml_priority + ml_priority_confidence.
    """
    # 1) LLM-класифікація
    try:
        res = route_with_llm(inc.title, inc.description)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM routing error: {e}")

    # 2) ML-оцінка пріоритету
    full_text = f"{inc.title}\n{inc.description}".strip()
    if full_text and ml_model.model is not None:
        try:
            ml_label, ml_conf = ml_model.predict_priority(full_text)
            # high/medium/low -> P1/P2/P3 (якщо потрібно відображати в тому ж форматі)
            map_to_p = {"high": "P1", "medium": "P2", "low": "P3"}

            res["ml_priority_raw"] = ml_label
            res["ml_priority"] = map_to_p.get(ml_label, ml_label)
            res["ml_priority_confidence"] = ml_conf
        except Exception as e:
            print("[ML] помилка під час прогнозу:", e)
            res["ml_priority"] = None
            res["ml_priority_confidence"] = None
    else:
        res["ml_priority"] = None
        res["ml_priority_confidence"] = None

    return res


# === Фронтенд ===

# монтуємо папку frontend як статику
if not FRONTEND_DIR.exists():
    # якщо тут ініціалізація впаде – буде видно одразу у консолі
    raise RuntimeError(f"Папка фронтенду не знайдена: {FRONTEND_DIR}")

app.mount(
    "/ui_llm_static",
    StaticFiles(directory=FRONTEND_DIR, html=True),
    name="ui_llm_static",
)


@app.get("/")
def root_redirect():
    """
    Редірект з кореня на інтерфейс.
    """
    return RedirectResponse(url="/ui_llm")


@app.get("/ui_llm")
def ui_llm():
    """
    Просто редірект на index.html у змонтованій статиці.
    """
    return RedirectResponse(url="/ui_llm_static/index.html")
