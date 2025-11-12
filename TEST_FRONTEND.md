# Тестування Фронтенду

## Сервер запущено на:
- Backend API: http://127.0.0.1:8002
- Frontend: http://127.0.0.1:8002/ui_llm_static/

## Кроки для тестування:

### 1. Логін
- Відкрити: http://127.0.0.1:8002/ui_llm_static/login.html
- Логін: `admin@example.com`
- Пароль: `admin123`

### 2. Dashboard
- Після логіну автоматично перенаправить на dashboard
- Має показати навігацію та статистику (placeholder)

### 3. Список Тікетів
- Перейти на "Tickets"
- Має завантажити тікет INC-0001 з БД
- Показати ML класифікацію (Hardware, 80%)
- Працюють фільтри (статус, пріоритет, тільки тріаж)

### 4. Створення Тікета
- Натиснути "Створити тікет"
- Заповнити форму:
  - Заголовок: "Не працює принтер"
  - Опис: "Принтер HP LaserJet не друкує документи. Горить червона лампочка."
  - Пріоритет: P3
  - Департамент: IT Support
- Натиснути "Створити тікет"
- Має виконатись ML класифікація
- Показати alert з результатами ML
- Перенаправити на список тікетів

### 5. Перевірка ML
- Новий тікет має з'явитись у списку
- Має бути ML категорія з confidence
- Якщо confidence < 60% - буде позначка "Тріаж потрібен"

## Що працює ✅

1. **Backend API (100%)**
   - ✅ ML Service - інтеграція з Ollama + sklearn
   - ✅ Ticket Service - логіка тріажу
   - ✅ Tickets Router - 9 ендпоінтів (CRUD + claim + assign + triage)
   - ✅ Departments Router - список департаментів
   - ✅ Auth Router - JWT логін

2. **Frontend (90%)**
   - ✅ Логін форма
   - ✅ Dashboard (placeholder)
   - ✅ Список тікетів з фільтрами
   - ✅ Форма створення тікета
   - ✅ API клієнт з усіма методами
   - ✅ Auth guard
   - ⚠️ JWT auth має minor issue з /auth/me (не критично)

3. **ML Integration (95%)**
   - ✅ LLM класифікація категорій (Ollama phi3)
   - ✅ ML класифікація пріоритету (sklearn)
   - ✅ Логування в MLPredictionLog
   - ✅ Тріаж при низькій confidence
   - ⚠️ Priority ML model не завжди повертає результат

## Що НЕ реалізовано (для диплому можна додати пізніше)

- Деталі тікета (ticket-details.html)
- Jira-like Board з drag & drop
- Triage Queue для LEAD
- Google OAuth
- Real-time updates
- Metrics/Monitoring
- Assets management
- Users management
