from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from .schemas import IncidentIn, LLMIncidentOut
from .llm_router import route_with_llm


app = FastAPI(
    title="Service Desk LLM Router",
    version="1.0.0",
    description=(
        "Прототип сервіс-деск системи, яка автоматично класифікує та "
        "маршрутизує інциденти за допомогою локальної LLM (Ollama)."
    ),
)


@app.post("/classify_llm", response_model=LLMIncidentOut)
def classify_llm(inc: IncidentIn):
    """
    Основний ендпоінт: LLM-маршрутизація інциденту.
    Використовує локальну LLM через Ollama (див. app.llm_router.route_with_llm).
    """
    try:
        res = route_with_llm(inc.title, inc.description)
    except Exception as e:
        # Якщо щось пішло не так (немає звʼязку з Ollama тощо) – HTTP 500
        raise HTTPException(status_code=500, detail=f"LLM routing error: {e}")

    return res


@app.get("/ui_llm", response_class=HTMLResponse)
@app.get("/", response_class=HTMLResponse)  # щоб головна сторінка теж відкривала UI
def ui_llm():
    """
    Єдиний інтерфейс для роботи з LLM-маршрутизатором.
    """
    return """
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8" />
    <title>LLM-маршрутизація інцидентів</title>
    <style>
        body {
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background: #0f172a;
            margin: 0;
            padding: 0;
        }
        .page {
            max-width: 900px;
            margin: 40px auto;
            background: #020617;
            padding: 24px 28px 32px;
            border-radius: 18px;
            box-shadow: 0 16px 40px rgba(15, 23, 42, 0.8);
            border: 1px solid #1e293b;
            color: #e5e7eb;
        }
        h1 {
            margin-top: 0;
            font-size: 24px;
            color: #e5e7eb;
        }
        p.subtitle {
            margin-top: 4px;
            margin-bottom: 24px;
            color: #9ca3af;
            font-size: 14px;
        }
        label {
            font-weight: 600;
            font-size: 14px;
            color: #cbd5f5;
            display: block;
            margin-bottom: 6px;
        }
        input[type="text"], textarea {
            width: 100%;
            box-sizing: border-box;
            border-radius: 10px;
            border: 1px solid #1f2937;
            padding: 10px 12px;
            font-size: 14px;
            outline: none;
            transition: border-color 0.2s, box-shadow 0.2s, background 0.2s;
            background: #020617;
            color: #e5e7eb;
            resize: vertical;
        }
        input[type="text"]:focus,
        textarea:focus {
            border-color: #38bdf8;
            box-shadow: 0 0 0 1px #38bdf8;
            background: #020617;
        }
        textarea {
            min-height: 130px;
        }
        .form-row {
            margin-bottom: 16px;
        }
        button {
            border: none;
            border-radius: 999px;
            padding: 10px 20px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            background: radial-gradient(circle at 0 0, #22c55e, #0ea5e9);
            color: #0b1120;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            box-shadow: 0 8px 30px rgba(34, 197, 94, 0.5);
            transition: transform 0.1s, box-shadow 0.1s, opacity 0.1s;
        }
        button:disabled {
            opacity: 0.5;
            cursor: default;
            box-shadow: none;
        }
        button:not(:disabled):hover {
            transform: translateY(-1px);
            box-shadow: 0 12px 40px rgba(56, 189, 248, 0.7);
        }
        .badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 600;
        }
        .badge-team {
            background: #1d293b;
            color: #e5e7eb;
        }
        .badge-p1 {
            background: #7f1d1d;
            color: #fee2e2;
        }
        .badge-p2 {
            background: #78350f;
            color: #fef3c7;
        }
        .badge-p3 {
            background: #14532d;
            color: #dcfce7;
        }
        .badge-urg-high {
            background: #b91c1c;
            color: #fee2e2;
        }
        .badge-urg-med {
            background: #92400e;
            color: #ffedd5;
        }
        .badge-urg-low {
            background: #065f46;
            color: #d1fae5;
        }
        .results {
            margin-top: 24px;
            padding-top: 16px;
            border-top: 1px solid #1e293b;
        }
        .explanation {
            margin-top: 10px;
            background: #020617;
            border-radius: 10px;
            padding: 10px 12px;
            font-size: 13px;
            color: #e5e7eb;
            border: 1px dashed #1e293b;
        }
        .footer {
            margin-top: 20px;
            font-size: 11px;
            color: #6b7280;
            text-align: right;
        }
        .error {
            color: #fecaca;
            font-size: 13px;
            margin-top: 8px;
        }
        .pill {
            border-radius: 999px;
            border: 1px solid #1e293b;
            padding: 6px 10px;
            font-size: 12px;
            display: inline-flex;
            gap: 6px;
            align-items: center;
        }
        .pill-dot {
            width: 8px;
            height: 8px;
            border-radius: 999px;
            background: #22c55e;
        }
    </style>
</head>
<body>
<div class="page">
    <h1>LLM-маршрутизація інцидентів</h1>
    <p class="subtitle">
        Інтелектуальний маршрутизатор на базі локальної мовної моделі (через Ollama): 
        визначає категорію, пріоритет, терміновість, команду та можливість авто-призначення.
    </p>

    <div class="form-row">
        <label for="title">Заголовок</label>
        <input id="title" type="text" placeholder="Наприклад: Весь офіс втратив доступ до VPN">
    </div>
    <div class="form-row">
        <label for="description">Опис інциденту</label>
        <textarea id="description" placeholder="Опишіть симптоми, масштаб проблеми, кількість користувачів, вплив на бізнес..."></textarea>
    </div>
    <div class="form-row">
        <button id="submitBtn">🤖 Класифікувати (LLM)</button>
        <span id="status" class="error"></span>
    </div>

    <div class="results" id="results-block" style="display: none;">
        <div id="main-result"></div>
        <div class="explanation" id="explanation"></div>
    </div>

    <div class="footer">
        LLM routing · /classify_llm · Service Desk prototype
    </div>
</div>

<script>
    const btn = document.getElementById("submitBtn");
    const statusEl = document.getElementById("status");
    const resultsBlock = document.getElementById("results-block");
    const mainResult = document.getElementById("main-result");
    const explanation = document.getElementById("explanation");

    function priorityBadgeClass(priority) {
        if (!priority) return "badge";
        const p = priority.toUpperCase();
        if (p === "P1") return "badge badge-p1";
        if (p === "P2") return "badge badge-p2";
        if (p === "P3") return "badge badge-p3";
        return "badge";
    }

    function urgencyBadgeClass(urg) {
        if (!urg) return "badge";
        const u = urg.toUpperCase();
        if (u === "HIGH") return "badge badge-urg-high";
        if (u === "MEDIUM") return "badge badge-urg-med";
        if (u === "LOW") return "badge badge-urg-low";
        return "badge";
    }

    btn.addEventListener("click", async () => {
        statusEl.textContent = "";
        resultsBlock.style.display = "none";
        mainResult.innerHTML = "";
        explanation.textContent = "";

        const title = document.getElementById("title").value.trim();
        const desc = document.getElementById("description").value.trim();

        if (!title && !desc) {
            statusEl.textContent = "Введіть хоча б заголовок або опис інциденту.";
            return;
        }

        btn.disabled = true;
        btn.textContent = "⏳ Обробка...";
        try {
            const resp = await fetch("/classify_llm", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "accept": "application/json"
                },
                body: JSON.stringify({ title: title, description: desc })
            });

            if (!resp.ok) {
                const txt = await resp.text();
                statusEl.textContent = "Помилка запиту: " + resp.status + " " + txt;
                return;
            }

            const data = await resp.json();
            console.log(data);

            const cat = data.category || "-";
            const pri = data.priority || "-";
            const urg = data.urgency || "-";
            const team = data.team || "-";
            const assignee = data.assignee || "не визначено";
            const autoAssign = data.auto_assign ? "Так, авто-призначення дозволено" : "Ні, потрібна ручна перевірка";

            const priClass = priorityBadgeClass(pri);
            const urgClass = urgencyBadgeClass(urg);

            mainResult.innerHTML = `
                <div style="display:flex;flex-direction:column;gap:10px;">
                    <div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;">
                        <span class="badge badge-team">Категорія: ${cat}</span>
                        <span class="${priClass}">Пріоритет: ${pri}</span>
                        <span class="${urgClass}">Терміновість: ${urg}</span>
                    </div>
                    <div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;">
                        <span class="pill">
                            <span class="pill-dot"></span>
                            Команда: <strong>${team}</strong>
                        </span>
                        <span class="pill">
                            Виконавець: <strong>${assignee}</strong>
                        </span>
                        <span class="pill">
                            Авто-призначення: <strong>${autoAssign}</strong>
                        </span>
                    </div>
                </div>
            `;

            explanation.textContent = data.reasoning || "Модель не надала явного пояснення.";

            resultsBlock.style.display = "block";

        } catch (err) {
            console.error(err);
            statusEl.textContent = "Не вдалося виконати запит: " + err;
        } finally {
            btn.disabled = false;
            btn.textContent = "🤖 Класифікувати (LLM)";
        }
    });
</script>
</body>
</html>
    """
