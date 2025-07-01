# en src/ref/migrations/0003_corregir_plantillas_sql.py

from django.db import migrations


def cargar_definicion_panorama_provincial_corregida(apps, schema_editor):
    """
    Esta función borra las definiciones existentes y las vuelve a crear con las
    plantillas SQL correctas.
    """
    Informe = apps.get_model('ref', 'Informe')
    Componente = apps.get_model('ref', 'Componente')
    InformeComposicion = apps.get_model('ref', 'InformeComposicion')

    # La función primero borra todo, asegurando una carga limpia.
    Informe.objects.all().delete()
    Componente.objects.all().delete()

    kpi_poblacion = Componente.objects.create(
        nombre="KPI Población",
        tipo_componente="KPI",
        estado='ACTIVO',
        parametros_requeridos={"params": ["provincia_id"]},
        config_visualizacion={"format": "int", "suffix": " hab."},
        # Corregido para usar el 'id' del modelo IndicadoresContexto
        plantilla_sql="SELECT poblacion_censo_2022 FROM indicadores_contexto_y_sicytar WHERE id = {{ provincia_id }};"
    )
    
    kpi_investigadores = Componente.objects.create(
        nombre="KPI Cantidad de Investigadores",
        tipo_componente="KPI",
        estado='ACTIVO',
        parametros_requeridos={"params": ["provincia_id"]},
        config_visualizacion={"format": "int", "suffix": " investigadores"},
        # CORRECCIÓN: 'investigador' en minúsculas y usando 'id'
        plantilla_sql="SELECT investigador FROM indicadores_contexto_y_sicytar WHERE id = {{ provincia_id }};"
    )
    
    kpi_tasa_investigadores = Componente.objects.create(
        nombre="KPI Tasa Investigadores por millón de hab.",
        tipo_componente="KPI",
        estado='ACTIVO',
        parametros_requeridos={"params": ["provincia_id"]},
        config_visualizacion={"format": "float", "suffix": " por millón hab."},
        # Corregido para usar el 'id' del modelo IndicadoresContexto
        plantilla_sql="SELECT tasa_inv_millon_hab FROM indicadores_contexto_y_sicytar WHERE id = {{ provincia_id }};"
    )

    comp_grafico_inversion = Componente.objects.create(
        nombre="Gráfico Comparativo de Inversión en I+D - Provincia vs Región y País",
        tipo_componente="GRAFICO.line",
        estado='ACTIVO',
        parametros_requeridos={"params": ["provincia_id"]},
        config_visualizacion={
            "layout": { "title": {"text": "Evolución de la Inversión en I+D"}, "xaxis": {"title": {"text": "Año"}}, "yaxis": {"title": {"text": "Monto (Pesos Constantes 2004)"}} }
        },
        # CORRECCIÓN: 'anio' en lugar de 'anio_id'
        plantilla_sql="""
            SELECT anio, unidad_territorial, SUM(monto_inversion_constante_2004) as inversion_constante
            FROM inversion_id_ract_esid_provincia_region_pais
            WHERE unidad_territorial IN (
                (SELECT provincia FROM ref_provincia WHERE provincia_id = {{ provincia_id }}),
                (SELECT region_cofecyt FROM ref_provincia WHERE provincia_id = {{ provincia_id }}),
                'País'
            )
            GROUP BY anio, unidad_territorial ORDER BY anio, unidad_territorial;
        """
    )

    informe_panorama = Informe.objects.create(
        nombre="Panorama Provincial",
        descripcion="Informe automático que presenta una visión general de los principales indicadores de C&T de una provincia.",
        estado='ACTIVO',
        version=1
    )

    InformeComposicion.objects.create(informe=informe_panorama, componente=kpi_poblacion, orden=10)
    InformeComposicion.objects.create(informe=informe_panorama, componente=kpi_investigadores, orden=20)
    InformeComposicion.objects.create(informe=informe_panorama, componente=kpi_tasa_investigadores, orden=30)
    InformeComposicion.objects.create(
        informe=informe_panorama,
        componente=comp_grafico_inversion,
        orden=40,
        config_override={"layout": {"title": {"text": "Inversión en I+D: {{ provincia_nombre }} vs. Región y País"}}}
    )

class Migration(migrations.Migration):

    dependencies = [
        ('ref', '0002_cargar_definicion_panorama_provincial'), # Depende de la migración anterior
    ]

    operations = [
        migrations.RunPython(cargar_definicion_panorama_provincial_corregida),
    ]