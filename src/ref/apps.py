from django.apps import AppConfig


class RefConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ref'

    def ready(self):
        # Importamos y registramos el template de Plotly
        from . import plotly_templates
        import plotly.io as pio

        pio.templates['poncho'] = plotly_templates.poncho_template
        pio.templates.default = 'poncho'
