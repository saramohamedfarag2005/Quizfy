from django import template

register = template.Library()

@register.filter
def get_item(d, key):
    """Safely get dict item by key in templates."""
    if not d:
        return None
    try:
        return d.get(key)
    except Exception:
        return None


@register.filter
def option_text(question, key):
    """
    Convert stored answer key into the visible option text.

    Supports BOTH:
    - Old style: question.options = {"A": "...", "B": "..."}
    - Current style: question.option1/2/3/4

    key can be: "A"/"B"/"C"/"D" OR 1/2/3/4 OR "option1"...
    """
    if question is None or key is None:
        return ""

    k = str(key).strip()

    # 1) If you ever used JSONField options
    opts = getattr(question, "options", None)
    if isinstance(opts, dict):
        return opts.get(k, "") or opts.get(k.upper(), "") or ""

    # 2) Normal DB fields option1..option4
    mapping = {
        "A": getattr(question, "option1", ""),
        "B": getattr(question, "option2", ""),
        "C": getattr(question, "option3", ""),
        "D": getattr(question, "option4", ""),
        "1": getattr(question, "option1", ""),
        "2": getattr(question, "option2", ""),
        "3": getattr(question, "option3", ""),
        "4": getattr(question, "option4", ""),
        "option1": getattr(question, "option1", ""),
        "option2": getattr(question, "option2", ""),
        "option3": getattr(question, "option3", ""),
        "option4": getattr(question, "option4", ""),
    }

    return mapping.get(k, "") or mapping.get(k.upper(), "") or ""
