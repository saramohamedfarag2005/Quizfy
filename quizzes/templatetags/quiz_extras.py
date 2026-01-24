from django import template

register = template.Library()

@register.filter(name="option_text")
def option_text(question, key):
    """
    Works with models that store options as fields like:
    option1, option2, option3, option4
    and keys like: 1/2/3/4 or "1"/"2"/"3"/"4"
    OR "A"/"B"/"C"/"D"
    """
    if question is None or key in (None, "", " "):
        return ""

    # Normalize key
    k = str(key).strip()

    # Support A/B/C/D
    map_abcd = {"A": "1", "B": "2", "C": "3", "D": "4"}
    if k.upper() in map_abcd:
        k = map_abcd[k.upper()]

    # Now k should be "1".."4"
    field_map = {
        "1": "option1",
        "2": "option2",
        "3": "option3",
        "4": "option4",
    }

    field_name = field_map.get(k)
    if not field_name:
        return ""

    return getattr(question, field_name, "") or ""


@register.filter
def get_item(d, key):
    if d is None:
        return None
    return d.get(key)