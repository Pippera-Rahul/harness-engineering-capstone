"""Simple, auditable context selection under a character budget."""


def select_context(items: list[dict], budget: int) -> dict:
    if budget < 0:
        raise ValueError("budget must be non-negative")
    ranked = sorted(items, key=lambda x: (-int(x.get("priority", 0)), str(x.get("id", ""))))
    selected, used = [], 0
    for item in ranked:
        text = str(item.get("text", ""))
        cost = len(text)
        if used + cost <= budget:
            selected.append({"id": item.get("id", ""), "text": text, "cost": cost})
            used += cost
    return {
        "selected": selected,
        "budget": budget,
        "used": used,
        "remaining": budget - used,
        "strategy": "priority_then_id",
    }


def compress_text(text: str, max_chars: int) -> str:
    if max_chars < 0:
        raise ValueError("max_chars must be non-negative")
    if len(text) <= max_chars:
        return text
    if max_chars <= 3:
        return "." * max_chars
    return text[:max_chars - 3] + "..."
