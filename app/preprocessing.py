import re
from typing import Dict

from deep_translator import GoogleTranslator


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


def detect_cyrillic(s: str) -> bool:
    """
    Перевірка, чи є в тексті кириличні символи.
    """
    return bool(re.search(r"[а-яА-ЯіїєґІЇЄҐ]", s))


def to_english(text: str) -> str:
    """
    Якщо текст кирилицею – перекладаємо на англійську.
    Якщо ні – повертаємо як є.
    У разі помилки перекладу – теж повертаємо оригінал.
    """
    text = text.strip()
    if not text:
        return text

    if detect_cyrillic(text):
        try:
            translated = GoogleTranslator(
                source="auto", target="en"
            ).translate(text)
            return translated
        except Exception:
            # На випадок, якщо зовнішній сервіс недоступний
            return text

    return text


def build_model_input(inc: Dict) -> Dict:
    """
    Формує вхід для ML-моделі:
    - склеюємо title + description;
    - при потребі перекладаємо на англійську;
    - нормалізуємо;
    - повертаємо dict з одним полем full_text.
    """
    raw_text = (inc.get("title", "") + " " + inc.get("description", "")).strip()
    text_en = to_english(raw_text)
    full_text = normalize_text(text_en)

    print("RAW TEXT:", raw_text)
    print("TEXT_EN:", text_en)
    print("FULL_TEXT:", full_text)

    return {"full_text": full_text}

