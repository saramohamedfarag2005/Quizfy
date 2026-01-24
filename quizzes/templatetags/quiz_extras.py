from django import template

register = template.Library()

@register.filter
def option_text(question, key):
    if not question or not key:
        return ""
    return question.options.get(key, "")

@register.filter
def get_item(d, key):
    if d is None:
        return None
    return d.get(key)