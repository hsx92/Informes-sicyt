# En src/ref/migrations/0006_limpiar_componentes.py (o el nombre que se haya generado)

from django.db import migrations


def borrar_componentes_existentes(apps, schema_editor):
    """
    Esta función borra todos los componentes para permitir un cambio
    en el esquema que no es compatible con los datos viejos.
    """
    Componente = apps.get_model('ref', 'Componente')
    Componente.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('ref', '0004_corregir_plantillas_sql_2'),
    ]

    operations = [
        migrations.RunPython(borrar_componentes_existentes),
    ]