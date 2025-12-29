from django import template

register = template.Library()

@register.filter
def option_text(question, option_key):
    if not option_key:
        return "(blank)"
    return question.option_text(option_key)
