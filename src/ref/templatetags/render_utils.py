from django import template
from jinja2 import Environment

register = template.Library()


@register.filter(name='render_dinamico')
def render_dinamico(template_string, params):
    """
    Filtro de plantilla que renderiza un string con un contexto.
    Uso: {{ componente.nombre|render_dinamico:params }}
    """
    if not isinstance(template_string, str) or "{{" not in template_string:
        return template_string

    env = Environment()
    template = env.from_string(template_string)
    return template.render(params)
