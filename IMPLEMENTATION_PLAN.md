# План імплементації Service Desk з ML (Частина 1/2)

## Поточний стан проекту

**Є:**
- FastAPI backend
- LLM router (Ollama/phi3)
- ML classifier (sklearn TF-IDF + LogReg)
- Простий UI для класифікації
- Базова схема даних (IncidentIn/Out)

**Потрібно додати:**
- База даних (PostgreSQL/SQLite)
- ORM (SQLAlchemy)
- Повна рольова модель (ADMIN/LEAD/AGENT/USER)
- Розширені моделі: User, Department, Asset, Ticket, Comment
- ML-поля в Ticket (confidence, acceptance, triage)
- Settings для конфігурації ML
- State machine для статусів
- Всі API endpoints
- Повноцінний UI

---

## Архітектура нової системи

```
incident_text_app/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app
│   ├── config.py                  # NEW: Settings, DB URL
│   ├── database.py                # NEW: SQLAlchemy setup
│   │
│   ├── models/                    # NEW: ORM models
│   │   ├── __init__.py
│   │   ├── user.py                # User model
│   │   ├── department.py          # Department model
│   │   ├── asset.py               # Asset model
│   │   ├── ticket.py              # Ticket model (з ML полями)
│   │   ├── comment.py             # TicketComment model
│   │   ├── ml_log.py              # MLPredictionLog model
│   │   └── settings.py            # Settings model
│   │
│   ├── schemas/                   # NEW: Pydantic schemas
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── department.py
│   │   ├── asset.py
│   │   ├── ticket.py
│   │   ├── comment.py
│   │   ├── settings.py
│   │   └── auth.py
│   │
│   ├── services/                  # NEW: Business logic
│   │   ├── __init__.py
│   │   ├── auth.py                # JWT, password hashing
│   │   ├── ticket_service.py      # Ticket lifecycle
│   │   ├── ml_service.py          # ML pipeline
│   │   ├── triage_service.py      # Triage logic
│   │   └── export_service.py      # ML data export
│   │
│   ├── routers/                   # API endpoints
│   │   ├── __init__.py
│   │   ├── auth.py                # NEW: /auth/*
│   │   ├── users.py               # NEW: /users/*
│   │   ├── departments.py         # NEW: /departments/*
│   │   ├── assets.py              # NEW: /assets/*
│   │   ├── tickets.py             # NEW: /tickets/* (повний CRUD)
│   │   ├── comments.py            # NEW: /comments/*
│   │   ├── settings.py            # NEW: /settings/*
│   │   └── ml.py                  # NEW: /ml/*
│   │
│   ├── core/                      # NEW: Core utilities
│   │   ├── __init__.py
│   │   ├── security.py            # JWT, permissions
│   │   ├── deps.py                # FastAPI dependencies
│   │   └── enums.py               # Role, Status, Priority, etc.
│   │
│   ├── ml_model.py                # Існуючий ML wrapper
│   ├── llm_router.py              # Існуючий LLM wrapper
│   └── preprocessing.py           # Існуючий preprocessing
│
├── frontend/                      # UI (React/Vue або HTML+JS)
│   ├── index.html
│   ├── login.html                 # NEW
│   ├── tickets.html               # NEW
│   ├── ticket-detail.html         # NEW
│   ├── create-ticket.html         # NEW
│   ├── assets.html                # NEW
│   ├── departments.html           # NEW
│   ├── users.html                 # NEW
│   ├── settings.html              # NEW
│   └── js/
│       ├── app.js
│       ├── api.js                 # API calls
│       └── auth.js                # Auth logic
│
├── migrations/                    # NEW: Alembic migrations
│   └── versions/
│
├── tests/                         # NEW: Tests
│   ├── test_auth.py
│   ├── test_tickets.py
│   ├── test_ml_pipeline.py
│   └── test_triage.py
│
├── alembic.ini                    # NEW
├── requirements.txt
└── README.md
```

---

## Етапи розробки (Частина 1/2)

### Етап 1: База даних та ORM (2-3 дні)

**1.1. Налаштування SQLAlchemy**
- [ ] Встановити `sqlalchemy`, `alembic`, `psycopg2-binary` (або `aiosqlite`)
- [ ] Створити `app/database.py` (engine, SessionLocal, Base)
- [ ] Створити `app/config.py` (DATABASE_URL, SECRET_KEY)

**1.2. Створити ORM моделі**
- [ ] `models/user.py` - User (id, email, hashed_password, role, is_lead, department_id)
- [ ] `models/department.py` - Department (id, name, description)
- [ ] `models/asset.py` - Asset (id, name, type, department_id, owner_id)
- [ ] `models/ticket.py` - Ticket (всі поля з §3 вимог)
- [ ] `models/comment.py` - TicketComment
- [ ] `models/ml_log.py` - MLPredictionLog
- [ ] `models/settings.py` - Settings (singleton table)

**1.3. Migrations**
- [ ] `alembic init migrations`
- [ ] Створити initial migration
- [ ] `alembic upgrade head`

---

### Етап 2: Аутентифікація та ролі (1-2 дні)

**2.1. Security**
- [ ] `core/security.py` - JWT токени, password hashing (bcrypt)
- [ ] `core/enums.py` - Role, Status, Priority, Category, TriageReason, MLMode
- [ ] `core/deps.py` - Dependencies: get_db, get_current_user, require_role

**2.2. Auth API**
- [ ] `routers/auth.py`
  - POST /auth/register
  - POST /auth/login (повертає JWT)
  - GET /auth/me

**2.3. Schemas**
- [ ] `schemas/auth.py` - Token, UserLogin, UserRegister
- [ ] `schemas/user.py` - UserOut, UserCreate, UserUpdate

---

### Етап 3: CRUD для основних сутностей (2-3 дні)

**3.1. Users (ADMIN only)**
- [ ] `routers/users.py`
  - GET /users (list, фільтри)
  - GET /users/{id}
  - POST /users (create)
  - PATCH /users/{id} (update)
  - DELETE /users/{id}

**3.2. Departments (ADMIN)**
- [ ] `routers/departments.py`
  - GET /departments
  - POST /departments
  - PATCH /departments/{id}
  - DELETE /departments/{id}

**3.3. Assets**
- [ ] `routers/assets.py`
  - GET /assets (з фільтрами за департаментом/власником)
  - GET /assets/my (для USER)
  - POST /assets (ADMIN/LEAD)
  - PATCH /assets/{id}
  - DELETE /assets/{id}

**3.4. Settings (ADMIN)**
- [ ] `routers/settings.py`
  - GET /settings (читати поточні)
  - PATCH /settings (оновити: ML включений, режим, пороги)

---

### Етап 4: Tickets - Життєвий цикл (3-4 дні)

**4.1. Ticket schemas**
- [ ] `schemas/ticket.py`
  - TicketCreate (title, description, category?, asset_id?, labels?)
  - TicketOut (всі поля + ML-поля)
  - TicketUpdate
  - TicketStatusUpdate
  - TicketAssign
  - TicketTriageResolve

**4.2. Ticket service**
- [ ] `services/ticket_service.py`
  - `create_ticket(user, data)` - логіка з §4:
    - Викликає ML
    - Перевіряє пороги
    - Встановлює triage_required/status
    - Зберігає в БД
  - `update_ticket_status(ticket, new_status, user)`
  - `assign_ticket(ticket, assignee_id, user)`
  - `claim_ticket(ticket, agent_user)` - self-assign
  - `resolve_triage(ticket, category, priority, assignee?, lead_user)`

**4.3. ML service**
- [ ] `services/ml_service.py`
  - `predict_ticket(ticket_id)` - викликає існуючі ML/LLM моделі
  - Повертає: category_ml, category_conf, priority_ml, priority_conf, model_version
  - Створює запис у MLPredictionLog
  - Перевіряє пороги з Settings

**4.4. Triage service**
- [ ] `services/triage_service.py`
  - `check_triage_required(ticket, ml_result, settings)` → bool + reason
  - `apply_ml_predictions(ticket, ml_result, settings, mode)` - AUTO_APPLY логіка

**4.5. Tickets API**
- [ ] `routers/tickets.py`
  - POST /tickets (створення - §4 логіка)
  - GET /tickets (list з фільтрами + permissions)
  - GET /tickets/{id}
  - PATCH /tickets/{id}/status
  - PATCH /tickets/{id}/assign (LEAD/ADMIN)
  - POST /tickets/{id}/claim (AGENT self-assign)
  - PATCH /tickets/{id}/priority (LEAD/ADMIN)
  - PATCH /tickets/{id}/triage/resolve (LEAD)
  - POST /tickets/{id}/ml/recalculate (LEAD/ADMIN)

---

### Етап 5: Коментарі (1 день)

**5.1. Comments**
- [ ] `routers/comments.py`
  - POST /tickets/{ticket_id}/comments
  - GET /tickets/{ticket_id}/comments
  - PATCH /comments/{id}
  - DELETE /comments/{id}

---

### Етап 6: ML Export (1 день)

**6.1. Export service**
- [ ] `services/export_service.py`
  - `export_incidents_for_ml()` - повертає CSV/JSON з:
    - title, description
    - category_ml, priority_ml, confidence
    - category_final, priority_final (з ticket)
    - triage_required, triage_reason
    - accepted flags
    - assignee, department
    - timestamps

**6.2. Export API**
- [ ] `routers/ml.py`
  - GET /ml/export/incidents (ADMIN)
  - GET /ml/stats (статистика: accuracy, triage rate)

---

### Етап 7: Frontend MVP (3-4 дні)

**7.1. Auth UI**
- [ ] LoginPage (email + password)
- [ ] JWT зберігання (localStorage)
- [ ] Logout

**7.2. Layout**
- [ ] SidebarLayout з навігацією (Dashboard, Tickets, Assets, Departments, Users, Settings)
- [ ] Показувати/ховати пункти за ролями

**7.3. Tickets UI**
- [ ] TicketsPage - таблиця з фільтрами:
  - Колонки: ID, Title, Status, Priority (manual + ML), Assignee, Department
  - Quick filters: My tickets, In triage, P1/P2, Unassigned
- [ ] CreateTicketPage - форма
- [ ] TicketDetailsPage:
  - Показати всі ML-поля (suggested, confidence, accepted)
  - Якщо triage_required - показати banner з triage_reason
  - Якщо LEAD: кнопка "Resolve Triage" → форма
  - Якщо AGENT + can self-assign: кнопка "Claim"
  - Коментарі

**7.4. Assets UI**
- [ ] AssetsPage - список з можливістю створення (ADMIN/LEAD)
- [ ] MyAssetsPage (USER)

**7.5. Admin UI**
- [ ] DepartmentsPage (ADMIN)
- [ ] UsersPage (ADMIN)
- [ ] SettingsPage (ADMIN) - форма налаштувань ML

---

### Етап 8: Тестування (2-3 дні)

**8.1. Unit tests**
- [ ] test_auth.py - реєстрація, логін, JWT
- [ ] test_tickets.py - створення, state transitions
- [ ] test_ml_pipeline.py - виклик ML, пороги
- [ ] test_triage.py - логіка тріажу
- [ ] test_permissions.py - RBAC

**8.2. Integration tests**
- [ ] test_scenarios.py - сценарії з §10:
  - ML вимкнено → TRIAGE
  - ML RECOMMEND → показати, не застосовувати
  - ML AUTO_APPLY + high conf → застосувати
  - ML AUTO_APPLY + low conf → TRIAGE
  - self-assign flow

**8.3. E2E tests (optional)**
- [ ] Selenium/Playwright - основні user flows

---

## Технології

### Backend
- **Framework:** FastAPI
- **ORM:** SQLAlchemy 2.0
- **DB:** PostgreSQL (або SQLite для dev)
- **Migrations:** Alembic
- **Auth:** python-jose (JWT), passlib (bcrypt)
- **ML:** scikit-learn (існуючий), Ollama (LLM)
- **Translation:** deep-translator

### Frontend
- **Option 1 (простий):** Vanilla JS + Fetch API + Tailwind CSS
- **Option 2 (рекомендую):** React + TypeScript + Tailwind + React Query
- **Option 3:** Vue 3 + TypeScript + Vite

### Додаткові пакети
```
sqlalchemy>=2.0
alembic>=1.13
psycopg2-binary>=2.9  # або aiosqlite
python-jose[cryptography]>=3.3
passlib[bcrypt]>=1.7
python-multipart>=0.0.6
```

---

## Приклад структури Ticket model

```python
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

class StatusEnum(str, enum.Enum):
    NEW = "NEW"
    TRIAGE = "TRIAGE"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"

class PriorityEnum(str, enum.Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"

class CategoryEnum(str, enum.Enum):
    HARDWARE = "Hardware"
    SOFTWARE = "Software"
    NETWORK = "Network"
    ACCESS = "Access"
    OTHER = "Other"

class TriageReasonEnum(str, enum.Enum):
    LOW_PRIORITY_CONF = "LOW_PRIORITY_CONF"
    LOW_CATEGORY_CONF = "LOW_CATEGORY_CONF"
    ML_DISABLED = "ML_DISABLED"
    MANUAL_FLAG = "MANUAL_FLAG"

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)

    # Status & Priority
    status = Column(SQLEnum(StatusEnum), default=StatusEnum.NEW, nullable=False)
    priority_manual = Column(SQLEnum(PriorityEnum), default=PriorityEnum.P3, nullable=False)
    category = Column(SQLEnum(CategoryEnum), nullable=True)

    # ML fields - Priority
    priority_ml_suggested = Column(SQLEnum(PriorityEnum), nullable=True)
    priority_ml_confidence = Column(Float, nullable=True)  # 0..1
    priority_accepted = Column(Boolean, default=False)

    # ML fields - Category
    category_ml_suggested = Column(SQLEnum(CategoryEnum), nullable=True)
    category_ml_confidence = Column(Float, nullable=True)  # 0..1
    category_accepted = Column(Boolean, default=False)

    # ML metadata
    ml_model_version = Column(String(50), nullable=True)

    # Triage
    triage_required = Column(Boolean, default=False)
    triage_reason = Column(SQLEnum(TriageReasonEnum), nullable=True)
    self_assign_locked = Column(Boolean, default=False)

    # Relations
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_to_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=True)

    # Metadata
    labels = Column(String(500), nullable=True)  # JSON string or comma-separated
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    # Relationships
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    assigned_to = relationship("User", foreign_keys=[assigned_to_user_id])
    department = relationship("Department")
    asset = relationship("Asset")
    comments = relationship("TicketComment", back_populates="ticket")
    ml_logs = relationship("MLPredictionLog", back_populates="ticket")
```

---

## Приклад Settings model

```python
class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True)  # Singleton - завжди 1 запис

    # ML
    feature_ml_enabled = Column(Boolean, default=True)
    ml_mode = Column(SQLEnum(MLModeEnum), default=MLModeEnum.RECOMMEND)  # RECOMMEND / AUTO_APPLY
    ml_conf_threshold_priority = Column(Float, default=0.6)
    ml_conf_threshold_category = Column(Float, default=0.6)

    # Agents
    agents_can_self_assign = Column(Boolean, default=True)
    agent_visibility_scope = Column(SQLEnum(VisibilityScopeEnum), default=VisibilityScopeEnum.DEPT)  # DEPT / ALL

    updated_at = Column(DateTime, nullable=False)
```

---

## Приклад логіки створення тікета

```python
async def create_ticket(
    db: Session,
    user: User,
    data: TicketCreate,
    ml_service: MLService,
    settings: Settings
) -> Ticket:
    # 1. Створити тікет
    ticket = Ticket(
        title=data.title,
        description=data.description,
        category=data.category,
        asset_id=data.asset_id,
        labels=data.labels,
        created_by_user_id=user.id,
        department_id=user.department_id or data.department_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(ticket)
    db.flush()  # отримати ID

    # 2. Якщо ML вимкнено
    if not settings.feature_ml_enabled:
        ticket.triage_required = True
        ticket.triage_reason = TriageReasonEnum.ML_DISABLED
        ticket.status = StatusEnum.TRIAGE
        db.commit()
        return ticket

    # 3. Викликати ML
    ml_result = await ml_service.predict_ticket(ticket.id)

    # Зберегти ML результати
    ticket.priority_ml_suggested = ml_result.priority
    ticket.priority_ml_confidence = ml_result.priority_conf
    ticket.category_ml_suggested = ml_result.category
    ticket.category_ml_confidence = ml_result.category_conf
    ticket.ml_model_version = ml_result.model_version

    # 4. Перевірити пороги
    priority_low = ml_result.priority_conf < settings.ml_conf_threshold_priority
    category_low = ml_result.category_conf < settings.ml_conf_threshold_category

    if priority_low or category_low:
        ticket.triage_required = True
        if priority_low and category_low:
            ticket.triage_reason = TriageReasonEnum.LOW_PRIORITY_CONF  # або обидва
        elif priority_low:
            ticket.triage_reason = TriageReasonEnum.LOW_PRIORITY_CONF
        else:
            ticket.triage_reason = TriageReasonEnum.LOW_CATEGORY_CONF
        ticket.status = StatusEnum.TRIAGE
    else:
        # 5. AUTO_APPLY або RECOMMEND
        if settings.ml_mode == MLModeEnum.AUTO_APPLY:
            ticket.priority_manual = ml_result.priority
            ticket.priority_accepted = True
            if not ticket.category:  # якщо не задано вручну
                ticket.category = ml_result.category
                ticket.category_accepted = True
        # RECOMMEND - нічого не робимо, просто показуємо
        ticket.status = StatusEnum.NEW

    db.commit()
    db.refresh(ticket)
    return ticket
```

---

## Наступні кроки

1. **Вибрати БД:** PostgreSQL (production) або SQLite (dev/test)
2. **Встановити залежності:**
   ```bash
   pip install sqlalchemy alembic psycopg2-binary python-jose[cryptography] passlib[bcrypt] python-multipart
   ```
3. **Почати з Етапу 1:** База даних та ORM
4. **Паралельно:** можна працювати над frontend structure

---

## Питання для уточнення

1. **БД:** PostgreSQL чи SQLite (для початку)?
2. **Frontend:** React/Vue чи простий HTML+JS?
3. **Розгортання:** Docker compose?
4. **Тестові дані:** згенерувати seed для розробки?
5. **CI/CD:** GitHub Actions?

Чекаю на другу частину вимог! 🚀
