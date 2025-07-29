# En src/ref/plotly_templates.py
import plotly.graph_objects as go

# Paleta de colores y tipografía basada en el sistema de diseño "Poncho"
PONCHO_PRIMARY_COLOR = '#0072BB'
PONCHO_TEXT_COLOR = '#333333'
PONCHO_BACKGROUND_COLOR = '#FFFFFF'
PONCHO_GRID_COLOR = '#ECF0F1'
PONCHO_COLOR_SEQUENCE = ['#2E7D32', '#FFC107', '#D32F2F', '#512DA8', '#0097A7', '#689F38']
PONCHO_FONT_FAMILY = "Encode Sans, sans-serif"

poncho_template = go.layout.Template(
    layout=go.Layout(
        font=dict(
            family=PONCHO_FONT_FAMILY,
            size=14,
            color=PONCHO_TEXT_COLOR
        ),
        title_font_size=24,
        paper_bgcolor=PONCHO_BACKGROUND_COLOR,
        plot_bgcolor=PONCHO_BACKGROUND_COLOR,
        colorway=PONCHO_COLOR_SEQUENCE,
        xaxis=dict(
            gridcolor=PONCHO_GRID_COLOR,
            linecolor=PONCHO_GRID_COLOR,
            zerolinecolor=PONCHO_GRID_COLOR,
        ),
        yaxis=dict(
            gridcolor=PONCHO_GRID_COLOR,
            linecolor=PONCHO_GRID_COLOR,
            zerolinecolor=PONCHO_GRID_COLOR,
        )
    )
)
