from django.db import models
from django.utils.text import slugify


class Informe(models.Model):
    class Estado(models.TextChoices):
        BORRADOR = 'BORRADOR', 'Borrador'
        ACTIVO = 'ACTIVO', 'Activo'
        ARCHIVADO = 'ARCHIVADO', 'Archivado'

    nombre = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, editable=False)
    descripcion = models.TextField(blank=True)
    version = models.PositiveSmallIntegerField(default=1)
    estado = models.CharField(
        max_length=10,
        choices=Estado.choices,
        default=Estado.BORRADOR
    )

    componentes = models.ManyToManyField(
        'Componente',
        through='InformeComposicion',
        related_name='informes'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Definición de Informe"
        verbose_name_plural = "Definiciones de Informes"
        ordering = ['nombre']

    def save(self, *args, **kwargs):
        self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} (v{self.version})"


class Componente(models.Model):
    class Estado(models.TextChoices):
        BORRADOR = 'BORRADOR', 'Borrador'
        ACTIVO = 'ACTIVO', 'Activo'
        ARCHIVADO = 'ARCHIVADO', 'Archivado'

    class Tipo(models.TextChoices):
        KPI = 'KPI', 'KPI'
        GRAFICO = 'GRAFICO', 'Gráfico'
        TABLA = 'TABLA', 'Tabla'
        TEXTO = 'TEXTO', 'Texto'

    class TipoGrafico(models.TextChoices):
        # Gráficos de Comparación / Relación
        LINE = 'line', 'Líneas'
        BAR = 'bar', 'Barras Verticales'
        BARH = 'barh', 'Barras Horizontales'
        SCATTER = 'scatter', 'Dispersión (Scatter Plot)'

        # Gráficos de Distribución
        HISTOGRAM = 'histogram', 'Histograma'
        BOX = 'box', 'Cajas (Box Plot)'

        # Gráficos de Proporción / Jerarquía
        PIE = 'pie', 'Torta / Anillo'
        TREEMAP = 'treemap', 'Mapa de Árbol (Treemap)'
        SUNBURST = 'sunburst', 'Explosión Solar (Sunburst)'

        # Gráficos Geográficos
        MAP = 'map', 'Mapa Coroplético'

    nombre = models.CharField(max_length=255, unique=True)
    descripcion = models.TextField(blank=True)
    version = models.PositiveSmallIntegerField(default=1)
    estado = models.CharField(
        max_length=10,
        choices=Estado.choices,
        default=Estado.BORRADOR
    )

    tipo_componente = models.CharField(
        max_length=20,
        choices=Tipo.choices,
        help_text="El tipo general del componente."
    )

    tipo_grafico = models.CharField(
        max_length=50,
        blank=True,
        choices=TipoGrafico.choices,
        help_text="Especificación del tipo de gráfico (ej: line, barh, pie)."
    )

    parametros_requeridos = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            'Lista de parámetros que la plantilla espera. '
            'Ej: ["provincia_id", "anio"]'
        )
    )
    config_visualizacion = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            'Configuración de visualización por defecto. '
            'Ej: {"title": "Título por Defecto"}'
        )
    )

    plantilla_sql = models.TextField(blank=True, null=True)
    plantilla_prompt = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Componente de Informe"
        verbose_name_plural = "Componentes de Informes"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} (v{self.version})"


class InformeComposicion(models.Model):
    informe = models.ForeignKey(Informe, on_delete=models.CASCADE)
    componente = models.ForeignKey(Componente, on_delete=models.CASCADE)
    orden = models.PositiveIntegerField()

    config_override = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            'Sobrescribe la configuración de visualización para este informe. '
            'Ej: {"title": "Título Específico"}'
        )
    )

    class Meta:
        verbose_name = "Composición de Informe"
        verbose_name_plural = "Composiciones de Informes"
        ordering = ['informe', 'orden']
        unique_together = ('informe', 'componente')

    def __str__(self):
        return (
            f"{self.informe.nombre} | {self.orden}: "
            f"{self.componente.nombre}"
        )
