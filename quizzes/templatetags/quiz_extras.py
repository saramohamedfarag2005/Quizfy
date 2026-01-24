from django import template

register = template.Library()


@register.filter
def option_text(question, selected):
    """
    Works with Question model that has: option1, option2, option3, option4
    selected might be: "A"/"B"/"C"/"D" OR "1"/"2"/"3"/"4"
    """
    if not question or not selected:
        return ""

    key = str(selected).strip().upper()

    mapping = {
        "A": question.option1,
        "B": question.option2,
        "C": question.option3,
        "D": question.option4,
        "1": question.option1,
        "2": question.option2,
        "3": question.option3,
        "4": question.option4,
    }

    val = mapping.get(key, "")
    return val or ""

@register.filter
def get_item(d, key):
    if d is None:
        return None
    return d.get(key)