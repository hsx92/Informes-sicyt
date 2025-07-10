from django.urls import path
from . import views

urlpatterns = [
    # Mapea la URL al a view generar_informe_api
    # La URL debe ser de la forma: /api/v1/informes/<informe_id>/generar/?provincia_id=<id>&anio=<anio>
    # 'informe_id' es un entero que representa el ID del informe a generar
    path('informes/<int:informe_id>/generar/', views.generar_informe_api, name='generar_informe_api'),
]
