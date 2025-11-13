import json
import textwrap
from typing import Any, Dict, Optional

import requests


# URL локального API Ollama
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
# Назва моделі, яку ти бачив у `ollama list`
OLLAMA_MODEL = "phi3"


def _build_prompt(title: str, description: str) -> str:
    """
    Формує інструкцію для локальної LLM.
    """

    incident_text = (title.strip() + "\n\n" + description.strip()).strip()

    prompt = f"""
    You are an intelligent IT Service Desk routing assistant.

    Your task:
    - Read an incident description (in Ukrainian or English).
    - Decide:
        * category: one of ["Network", "VPN", "Workstation", "Application", "Billing", "Other"]
        * priority: one of ["P1", "P2", "P3"]
        * urgency: one of ["HIGH", "MEDIUM", "LOW"]
        * team: one of ["ServiceDesk_L1", "Network_L2", "DBA", "Helpdesk_Onsite"]
        * assignee: a short identifier of a person in that team, or null if unknown.
        * auto_assign: true if the incident can be assigned automatically without human review, otherwise false.
        * reasoning: short explanation (1-3 sentences) why you selected this category, priority and team.

    Rules:
    - P1 = critical business impact (system down, many users, production).
    - P2 = important, but not a total outage.
    - P3 = non-urgent or informational.
    - If VPN / network in the whole office is down => usually P1 and team = "Network_L2".
    - If it is a billing or payment question => category "Billing", team "ServiceDesk_L1", priority P3.

    Return STRICTLY valid JSON with the following structure:

    {{
      "category": "string",
      "priority": "P1" | "P2" | "P3",
      "urgency": "HIGH" | "MEDIUM" | "LOW",
      "team": "string",
      "assignee": "string or null",
      "auto_assign": true or false,
      "reasoning": "string"
    }}

    Incident description:
    \"\"\"{incident_text}\"\"\"
    """
    return textwrap.dedent(prompt).strip()


def _call_ollama(prompt: str) -> str:
    """
    Виклик локальної моделі через Ollama.
    Повертає текст з поля "response" або весь JSON як текст.
    """

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }

    resp = requests.post(OLLAMA_URL, json=payload, timeout=120)

    # Якщо сервер живий, але status!=200 – все одно намагаємось прочитати JSON,
    # щоб не зривати все в except без потреби.
    try:
        data = resp.json()
    except Exception:
        # Якщо взагалі не JSON – просто повертаємо сирий текст
        return resp.text

    content = data.get("response")
    if content:
        return str(content).strip()

    # Якщо поле "response" відсутнє – повертаємо весь JSON як текст
    return json.dumps(data, ensure_ascii=False)


def _extract_json_block(text: str) -> Optional[Dict[str, Any]]:
    """
    Прагнемо дістати JSON навіть якщо модель написала щось довкола.
    Якщо JSON не знайдено або не парситься – повертаємо None.
    """

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None

    candidate = text[start : end + 1]

    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None


def _fallback_routing(title: str, description: str) -> Dict[str, Any]:
    """
    Резервний варіант, якщо до Ollama взагалі неможливо достукатись
    (порт, мережа, відсутній сервіс тощо).
    """

    text = (title + " " + description).lower()

    if "vpn" in text or "мереж" in text or "network" in text:
        category = "Network"
        team = "Network_L2"
        priority = "P1" if "весь" in text or "всі" in text or "all" in text else "P2"
        urgency = "HIGH"
    elif "рахунк" in text or "оплат" in text or "invoice" in text or "billing" in text:
        category = "Billing"
        team = "ServiceDesk_L1"
        priority = "P3"
        urgency = "MEDIUM"
    else:
        category = "Other"
        team = "ServiceDesk_L1"
        priority = "P3"
        urgency = "LOW"

    auto_assign = priority != "P1"

    return {
        "category": category,
        "priority": priority,
        "urgency": urgency,
        "team": team,
        "assignee": None,
        "auto_assign": auto_assign,
        "reasoning": (
            "Інцидент оброблено за резервними правилами, оскільки LLM недоступна "
            "або сталася помилка під час виклику моделі."
        ),
    }


def route_with_llm(title: str, description: str) -> Dict[str, Any]:
    """
    Основна функція, яку викликає FastAPI.

    Сценарій:
    1) Формуємо prompt.
    2) Пытаемся викликати Ollama (_call_ollama).
       - Якщо повністю впав запит (нема зʼєднання) → fallback.
    3) Пробуємо витягти JSON із відповіді.
       - Якщо JSON є → використовуємо його поля.
       - Якщо JSON немає → використовуємо текст як reasoning і додаємо розумні дефолти.
    """

    prompt = _build_prompt(title, description)

    try:
        raw = _call_ollama(prompt)
        print("[Ollama raw response]", raw)
    except Exception as e:
        # Справжня помилка підключення – тільки тут йдемо у fallback
        print("LLM routing via Ollama failed completely, using fallback. Error:", e)
        return _fallback_routing(title, description)

    parsed = _extract_json_block(raw)

    if parsed is None:
        # Модель не дотрималась формату JSON, але відповіла текстом.
        # Не провалюємось у rule-based, а просто повертаємо цей текст як пояснення.
        return {
            "category": "Other",
            "priority": "P3",
            "urgency": "LOW",
            "team": "ServiceDesk_L1",
            "assignee": None,
            "auto_assign": True,
            "reasoning": raw,
        }

    # Якщо JSON є – акуратно дістаємо поля
    category = parsed.get("category", "Other")
    priority = parsed.get("priority", "P3")
    urgency = parsed.get("urgency", "LOW")
    team = parsed.get("team", "ServiceDesk_L1")
    assignee = parsed.get("assignee")
    auto_assign = bool(parsed.get("auto_assign", False))
    reasoning = parsed.get("reasoning", raw)

    return {
        "category": category,
        "priority": priority,
        "urgency": urgency,
        "team": team,
        "assignee": assignee,
        "auto_assign": auto_assign,
        "reasoning": reasoning,
    }
