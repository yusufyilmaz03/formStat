"""Ham cevap değerlerini soru tipine göre normalize eder."""
from __future__ import annotations

from ..models import Answer, Question


def _to_float(value) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip().replace(",", ".")
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _split_multi(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    # CSV'de çoklu seçim genelde ", " ile ayrılır
    return [part.strip() for part in str(value).split(",") if part.strip()]


def build_answer(question: Question, value) -> Answer | None:
    """Bir soru + ham değerden Answer nesnesi üretir. Boşsa None döner."""
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return None

    ans = Answer(question_id=question.id)

    if question.type in {"number", "linear_scale"}:
        num = _to_float(value)
        if num is None:
            return None
        ans.value_number = num
        ans.value_text = str(value)
    elif question.type == "multi_choice":
        opts = _split_multi(value)
        if not opts:
            return None
        ans.value_options = opts
        ans.value_text = ", ".join(opts)
    else:
        # short_text, long_text, single_choice, dropdown, date, email
        ans.value_text = str(value).strip()

    return ans
