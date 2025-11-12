# Service Desk React Frontend

Сучасний React фронтенд з усіма можливостями Jira-like інтерфейсу.

## Функціонал

✅ **Реалізовано:**
- Login / Auth
- Tickets List з фільтрами
- Ticket Details Modal
- Create Ticket Form
- Jira-like Board з Drag & Drop
- ML Badges з confidence
- Priority/Status badges
- Responsive дизайн

📊 **Заготовки для майбутнього:**
- Analytics Dashboard з графіками
- ML Performance Charts
- Triage Queue Statistics
- Agent Performance Metrics

## Tech Stack

- **React 18** - UI фреймворк
- **Vite** - Build tool (швидша збірка)
- **React Router** - Навігація
- **Zustand** - State management (легший за Redux)
- **Axios** - HTTP клієнт
- **React Beautiful DnD** - Drag & Drop для Board
- **Recharts** - Графіки та аналітика
- **Tailwind CSS** - Стилізація
- **Lucide React** - Іконки

## Встановлення

```bash
cd frontend-react
npm install
```

## Запуск

```bash
# Development сервер (порт 3000)
npm run dev

# Production build
npm build

# Preview production build
npm run preview
```

## Структура проекту

```
frontend-react/
├── src/
│   ├── components/         # React компоненти
│   │   ├── Layout/        # Navbar, Sidebar
│   │   ├── Tickets/       # TicketCard, TicketList, TicketModal
│   │   ├── Board/         # KanbanBoard, Column, DraggableCard
│   │   ├── Charts/        # Analytics компоненти (заготовки)
│   │   └── common/        # Button, Badge, Modal, etc.
│   ├── pages/             # Сторінки
│   │   ├── Login.jsx
│   │   ├── Dashboard.jsx
│   │   ├── TicketsPage.jsx
│   │   ├── BoardPage.jsx
│   │   └── AnalyticsPage.jsx  # З графіками (заготовка)
│   ├── services/          # API клієнт
│   │   └── api.js
│   ├── stores/            # Zustand stores
│   │   ├── useAuthStore.js
│   │   └── useTicketsStore.js
│   ├── hooks/             # Custom hooks
│   ├── utils/             # Утіліти
│   ├── App.jsx            # Main app
│   └── main.jsx           # Entry point
├── package.json
├── vite.config.js
└── tailwind.config.js
```

## API

Підключається до FastAPI бекенду на `http://127.0.0.1:8003`

Vite proxy налаштований: `/api/*` → `http://127.0.0.1:8003/*`

## Особливості

### 1. Jira-like Board
- Drag & Drop між колонками (NEW → IN_PROGRESS → RESOLVED → CLOSED)
- Swimlanes за департаментами
- Quick filters
- ML badges на картках

### 2. Ticket Details Modal
- Повна інформація про тікет
- ML predictions з confidence
- Зміна статусу/пріоритету
- Claim/Assign функції
- Comments (заготовка)

### 3. Analytics Dashboard (Заготовка)
Компоненти для майбутніх графіків:
- **MLPerformanceChart** - Accuracy ML моделі в часі
- **PriorityDistributionChart** - Розподіл за пріоритетами
- **TriageStatsChart** - Статистика тріажу
- **ResponseTimeChart** - Час відгуку агентів

### 4. State Management
Zustand stores для:
- Authentication (token, user)
- Tickets (list, filters, selected)
- Board (columns, drag state)
- UI (модалки, alerts)

## Для диплому

Система демонструє:
1. ✅ ML інтеграцію з візуалізацією confidence
2. ✅ Тріаж workflow
3. ✅ RBAC (різні view для USER/AGENT/LEAD/ADMIN)
4. 📊 Заготовки для аналітики ML performance
5. 🎨 Сучасний UX як у Jira

## Next Steps

1. `npm install` - встановити залежності
2. `npm run dev` - запустити dev сервер
3. Відкрити http://localhost:3000
4. Login: admin@example.com / admin123

Backend має бути запущений на порту 8003!
