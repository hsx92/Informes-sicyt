from django.db import models


class Provincia(models.Model):
    provincia_id = models.IntegerField(primary_key=True, help_text="Identificador numérico único")
    nombre = models.CharField(max_length=100, db_column='provincia', help_text="Nombre oficial completo de la provincia")
    codigo_indec = models.CharField(max_length=20, blank=True, null=True, help_text="Código oficial según INDEC")
    region_mincyt = models.CharField(max_length=100, blank=True, null=True, help_text="Región según MINCyT")
    region_iso = models.CharField(max_length=20, blank=True, null=True, help_text="Código de provincia según ISO 3166-2:AR")
    region_cofecyt = models.CharField(max_length=100, blank=True, null=True, help_text="Región según COFECYT")

    class Meta:
        db_table = 'ref_provincia'
        verbose_name = "Provincia"
        verbose_name_plural = "Provincias"

    def __str__(self):
        return self.nombre


class InversionID(models.Model):
    id = models.AutoField(primary_key=True)
    anio = models.IntegerField(help_text="Año al que corresponde el dato de inversión")
    nivel_agregacion = models.CharField(max_length=50, help_text="Nivel geográfico (País, Región, Provincia)")
    unidad_territorial = models.CharField(max_length=100, help_text="Nombre de la locación geográfica")
    tipo_institucion_ract = models.CharField(max_length=100, blank=True, null=True, help_text="Tipo de institución que realiza la inversión")
    monto_inversion = models.DecimalField(max_digits=20, decimal_places=2, help_text="Monto en pesos corrientes")
    monto_inversion_constante_2004 = models.DecimalField(max_digits=20, decimal_places=2, help_text="Monto en pesos constantes de 2004")

    class Meta:
        db_table = 'inversion_id_ract_esid_provincia_region_pais'
        verbose_name = "Inversión en I+D"
        verbose_name_plural = "Inversiones en I+D"

    def __str__(self):
        return f"{self.unidad_territorial} ({self.anio_id}) - ${self.monto_inversion}"


class IndicadoresContexto(models.Model):
    id = models.IntegerField(primary_key=True, help_text="Identificador único de la provincia")
    provincia = models.CharField(max_length=100, help_text="Nombre oficial completo de la provincia")
    region_cofecyt = models.CharField(max_length=100, blank=True, null=True, help_text="Región según COFECYT")
    poblacion_censo_2022 = models.IntegerField(null=True, blank=True)
    superficie = models.FloatField(null=True, blank=True)
    vab_cepal_2022 = models.BigIntegerField(null=True, blank=True, help_text="Valor Agregado Bruto provincial del año 2022")
    tasas_actividad_eph_3trim_2024 = models.FloatField(null=True, blank=True)
    tasa_empleo_3trim_2024 = models.FloatField(null=True, blank=True)
    tasa_desocupacion_eph_3trim_2024 = models.FloatField(null=True, blank=True)
    cant_empresas_sipa_2022 = models.IntegerField(null=True, blank=True)
    trabajo_registrado_sipa_2024 = models.IntegerField(null=True, blank=True)
    exportaciones_millones_uss_opex_2023 = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    pea_miles_eph_3trim_2024 = models.FloatField(null=True, blank=True)
    pea_miles_censo_2022 = models.FloatField(null=True, blank=True)
    becario_id = models.IntegerField(null=True, blank=True)
    docente = models.IntegerField(null=True, blank=True)
    investigador = models.IntegerField(null=True, blank=True)
    otro_personal = models.IntegerField(null=True, blank=True, help_text="Otro personal de la institución de CyT")
    tasa_inv_millon_hab = models.FloatField(null=True, blank=True, help_text="Tasa de investigadores por cada millón de habitantes")
    tasa_inv_1000_pea = models.FloatField(null=True, blank=True, help_text="Tasa de investigadores por cada mil personas de la PEA")

    class Meta:
        db_table = 'indicadores_contexto_y_sicytar'
        verbose_name = "Indicador de Contexto y SICYTAR"
        verbose_name_plural = "Indicadores de Contexto y SICYTAR"

    def __str__(self):
        return self.provincia.nombre


class RRHHsicytar(models.Model):
    id = models.AutoField(primary_key=True)
    anio = models.IntegerField()
    nivel_agregacion = models.CharField(max_length=50)
    unidad_territorial = models.CharField(max_length=100)
    tipo_personal_sicytar = models.CharField(max_length=100)
    es_conicet = models.CharField(max_length=10)
    sexo_descripcion = models.CharField(max_length=50)
    gran_area_experticia = models.CharField(max_length=100)
    cant_personas = models.IntegerField()

    class Meta:
        db_table = 'rrhh_sicytar_agregado_provincia_region_pais'
        verbose_name = "RRHH SICYTAR Agregado"
        verbose_name_plural = "RRHH SICYTAR Agregados"


class RRHHract(models.Model):
    id = models.AutoField(primary_key=True)
    provincia_id = models.IntegerField()
    anio = models.IntegerField()
    tipo_institucion_ract = models.CharField(max_length=100)
    tipo_personal = models.CharField(max_length=100)
    tipo_jornada = models.CharField(max_length=50)
    valor = models.FloatField(help_text="Cantidad de personas, puede ser EAF")

    class Meta:
        db_table = 'rrhh_ract_esid'
        verbose_name = "RRHH RACT/ESID"
        verbose_name_plural = "RRHH RACT/ESID"


class InversionEmpresariaSector(models.Model):
    id = models.AutoField(primary_key=True)
    anio = models.IntegerField()
    nivel_agregacion = models.CharField(max_length=50)
    unidad_territorial = models.CharField(max_length=100)
    sector_clae = models.CharField(max_length=255)
    monto_inversion = models.DecimalField(max_digits=20, decimal_places=2)
    monto_inversion_constante_2004 = models.DecimalField(max_digits=20, decimal_places=2)

    class Meta:
        db_table = 'esid_inversion_sectores_provincia_region_pais'
        verbose_name = "Inversión Empresaria por Sector"
        verbose_name_plural = "Inversiones Empresarias por Sector"


class Patente(models.Model):
    id = models.AutoField(primary_key=True)
    lens_id = models.CharField(max_length=255, help_text="Identificador único de la patente en Lens")
    application_number = models.CharField(max_length=255, null=True, blank=True)
    anio = models.IntegerField()
    provincia = models.CharField(max_length=100, null=True, blank=True)
    region_cofecyt = models.CharField(max_length=100, null=True, blank=True)
    renaorg_id = models.CharField(max_length=50, null=True, blank=True)
    institucion = models.CharField(max_length=255, null=True, blank=True)
    es_institucion_nacional = models.CharField(max_length=10, null=True, blank=True)
    letra_ipc_descripcion = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'patentes_desagregadas_ipc_provincia_region_pais'
        verbose_name = "Patente Desagregada"
        verbose_name_plural = "Patentes Desagregadas"


class Proyecto(models.Model):
    id = models.AutoField(primary_key=True)
    proyecto_id = models.IntegerField()
    nivel_agregacion = models.CharField(max_length=50)
    unidad_territorial = models.CharField(max_length=100)
    anio_inicio = models.IntegerField()
    institucion_financiadora = models.CharField(max_length=255, null=True, blank=True)
    tmp_fondo_anpcyt = models.CharField(max_length=100, null=True, blank=True)
    tipo_proyecto_cyt = models.CharField(max_length=100, null=True, blank=True)
    gran_area = models.CharField(max_length=100, null=True, blank=True)
    tipo_organizacion_ejecutora = models.CharField(max_length=100, null=True, blank=True)
    monto_financiado_adjudicado_prorrateado = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    monto_total_adjudicado_prorrateado = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    monto_financiado_adjudicado_constante_2004_prorrateado = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    monto_total_adjudicado_constante_2004_prorrateado = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = 'proyectos_provincia_region_pais_renaprod'
        verbose_name = "Proyecto"
        verbose_name_plural = "Proyectos"


class ProductoCientifico(models.Model):
    id = models.AutoField(primary_key=True)
    producto_id = models.IntegerField()
    anio_publica = models.IntegerField(null=True, blank=True)
    unidad_territorial = models.CharField(max_length=100)
    tipo_producto_cientifico = models.CharField(max_length=255, null=True, blank=True)
    revista_sjr = models.CharField(max_length=255, null=True, blank=True)
    gran_area = models.CharField(max_length=100, null=True, blank=True)
    nivel_agregacion = models.CharField(max_length=50)

    class Meta:
        db_table = 'productos_provincia_region_pais_renaprod'
        verbose_name = "Producto Científico"
        verbose_name_plural = "Productos Científicos"


class ExportacionNivelTecnologico(models.Model):
    id = models.AutoField(primary_key=True)
    anio = models.IntegerField()
    nivel_agregacion = models.CharField(max_length=50)
    unidad_territorial = models.CharField(max_length=100)
    enfoque_industria = models.CharField(max_length=100, db_column='ITEnfoqueindustria')
    fob_millones_uss = models.DecimalField(max_digits=20, decimal_places=2)

    class Meta:
        db_table = 'expo_nivel_tecnologico_provincia_region_pais'
        verbose_name = "Exportación por Nivel Tecnológico"
        verbose_name_plural = "Exportaciones por Nivel Tecnológico"


class ExportacionTop5(models.Model):
    id = models.AutoField(primary_key=True)
    region_cofecyt = models.CharField(max_length=100)
    provincia = models.CharField(max_length=100)
    gran_rubro = models.CharField(max_length=255)
    y2021 = models.DecimalField(max_digits=20, decimal_places=2, db_column='2021', null=True, blank=True)
    y2022 = models.DecimalField(max_digits=20, decimal_places=2, db_column='2022', null=True, blank=True)
    y2023 = models.DecimalField(max_digits=20, decimal_places=2, db_column='2023', null=True, blank=True)
    y2024 = models.DecimalField(max_digits=20, decimal_places=2, db_column='2024', null=True, blank=True)

    class Meta:
        db_table = 'expo_por_provincia_top5'
        verbose_name = "Top 5 Productos Exportados por Provincia"
        verbose_name_plural = "Top 5 Productos Exportados por Provincia"


class ExportacionTecnologicaDestino(models.Model):
    id = models.AutoField(primary_key=True)
    anio = models.IntegerField()
    provincia = models.CharField(max_length=100, db_column= "cod_prov", null=True, blank=True)
    intensidad_tecnologica = models.BooleanField(help_text="True si alta, False si es baja")
    pais_destino = models.CharField(max_length=100)
    fob_millones_sum = models.DecimalField(max_digits=20, decimal_places=2)

    class Meta:
        db_table = 'expo_tecno_destino'
        verbose_name = "Exportación Tecnológica por Destino"
        verbose_name_plural = "Exportaciones Tecnológicas por Destino"


class PercepcionSocial(models.Model):
    id = models.AutoField(primary_key=True)
    anio = models.IntegerField()
    indicador = models.CharField(max_length=255)
    variable = models.CharField(max_length=255)
    nivel_agregacion = models.CharField(max_length=50)
    unidad_territorial = models.CharField(max_length=100)
    valor = models.FloatField(help_text="Generalmente un porcentaje")

    class Meta:
        db_table = 'percepcion_final'
        verbose_name = "Encuesta de Percepción Social"
        verbose_name_plural = "Encuestas de Percepción Social"


class UnidadID(models.Model):
    organizacion_id = models.IntegerField(primary_key=True)
    organizacion = models.CharField(max_length=255)
    nivel_1 = models.CharField(max_length=255, help_text="Institución principal de la cual depende")
    provincia = models.CharField(max_length=100)

    class Meta:
        db_table = 'listado_unidades_de_id'
        verbose_name = "Unidad de I+D"
        verbose_name_plural = "Unidades de I+D"


class EquipamientoSSNN(models.Model):
    id = models.AutoField(primary_key=True)
    unidad_territorial = models.CharField(max_length=100)
    sistema_nacional = models.CharField(max_length=255)
    cant_equipos = models.IntegerField()
    nivel_agregacion = models.CharField(max_length=50)

    class Meta:
        db_table = 'equipos_ssnn_provincia_region_pais'
        verbose_name = "Equipamiento SSNN"
        verbose_name_plural = "Equipamientos SSNN"


class InversionArticulosPorInvestigador(models.Model):
    id = models.AutoField(primary_key=True)
    anio = models.IntegerField()
    nivel_agregacion = models.CharField(max_length=50)
    unidad_territorial = models.CharField(max_length=100)
    monto_inversion = models.DecimalField(max_digits=20, decimal_places=2)
    cant_investigadores = models.IntegerField()
    cant_articulos = models.IntegerField()
    inversion_investigador = models.DecimalField(max_digits=20, decimal_places=2)
    articulos_investigador = models.FloatField()

    class Meta:
        db_table = 'inversion_y_articulos_por_investigador_provincia_region_pais'
        verbose_name = "Ratio Inversión-Artículo por Investigador"
        verbose_name_plural = "Ratios Inversión-Artículo por Investigador"


class ProyectoPFI(models.Model):
    id_pfi = models.CharField(max_length=100, primary_key=True)
    anio = models.IntegerField()
    cupo = models.CharField(max_length=50)
    region_cofecyt = models.CharField(max_length=100)
    provincia = models.CharField(max_length=100)
    tema = models.CharField(max_length=255)
    sector = models.CharField(max_length=255)
    vertical = models.CharField(max_length=255)
    tecnologias = models.TextField()
    vertical_tecnologia = models.TextField()

    class Meta:
        db_table = 'proyectos_pfi'
        verbose_name = "Proyecto Federal de Innovación (PFI)"
        verbose_name_plural = "Proyectos Federales de Innovación (PFI)"