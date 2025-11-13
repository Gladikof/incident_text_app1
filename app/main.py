from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import engine, Base
from app.routers import auth

# Legacy imports (для старого /classify_llm endpoint)
from app.legacy_schemas import IncidentIn, LLMIncidentOut
from app.llm_router import route_with_llm
from app.ml_model import ml_model

# === Створення таблиць БД ===
# Base.metadata.create_all(bind=engine)  # Не потрібно, бо є Alembic

# === Шляхи ===
FRONTEND_DIR = settings.FRONTEND_DIR

print(f"[DEBUG] FRONTEND_DIR = {FRONTEND_DIR}  exists={FRONTEND_DIR.exists()}")
print(f"[DEBUG] DATABASE_URL = {settings.DATABASE_URL}")

app = FastAPI(
    title="Service Desk ML System",
    version="2.0.0",
    description=(
        "Service Desk система з ML-класифікацією, тріажем та рольовою моделлю. "
        "Дипломна робота: Методика автоматизованої класифікації та пріоритизації інцідентів."
    ),
)

# === CORS ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Routers ===
from app.routers import tickets, departments, users, ml_logs

app.include_router(auth.router)
app.include_router(tickets.router)
app.include_router(departments.router)
app.include_router(users.router)
app.include_router(ml_logs.router)


@app.on_event("startup")
def _load_ml():
    """
    Завантаження ML-моделі при старті бекенду.
    """
    try:
        ml_model.load()
    except Exception as e:
        print("[ML] ERROR: Не вдалося завантажити модель:", e)


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
    Редірект з кореня на login.
    """
    return RedirectResponse(url="/ui_llm_static/login.html")


@app.get("/ui_llm")
def ui_llm():
    """
    Legacy: редірект на старий UI.
    """
    return RedirectResponse(url="/ui_llm_static/index.html")

