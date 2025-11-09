Incident Text-based Classifier
==============================

Цей проєкт реалізує прототип магістерської роботи:
«Методика автоматизованої класифікації та пріоритизації інцидентів
у сервіс-деск системі із застосуванням машинного навчання».

Модель навчається на відкритому датасеті `Tobi-Bueck/customer-support-tickets`
(HuggingFace) і вміє з тексту (title + description):

- визначати категорію тікета (queue);
- визначати пріоритет (priority);
- працювати з україномовним текстом через автоматичний переклад на англійську.

Основні компоненти:
- training/train_hf_tickets.py — завантаження датасету та навчання двох моделей;
- app/main.py — FastAPI-сервіс з ендпоінтом /classify_text;
- app/preprocessing.py — нормалізація тексту та переклад укр → англ;
- app/model.py — завантаження моделей;
- app/schemas.py — Pydantic-схеми для API.

Кроки запуску (приклад для Windows, Python 3.11+):

    python -m venv .venv
    .venv\Scripts\activate
    python -m pip install --upgrade pip setuptools wheel
    pip install -r requirements.txt

    # навчити моделі
    python training/train_hf_tickets.py

    # запустити API
    uvicorn app.main:app --reload --port 8000

Після запуску API документація буде доступна за адресою:
http://127.0.0.1:8000/docs
