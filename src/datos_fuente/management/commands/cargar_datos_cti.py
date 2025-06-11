import os
import pandas as pd
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction
from datos_fuente.models import (
    Provincia, InversionID, IndicadoresContexto, RRHHsicytar, RRHHract,
    InversionEmpresariaSector, Patente, Proyecto, ProductoCientifico,
    ExportacionNivelTecnologico, ExportacionTop5, ExportacionTecnologicaDestino,
    PercepcionSocial, UnidadID, EquipamientoSSNN,
    InversionArticulosPorInvestigador, ProyectoPFI
)

# Mapeo de nombres de archivo a modelos de Django
ARCHIVOS_A_CARGAR = {
    'ref_provincia.csv': Provincia,
    'inversion_id_ract_esid_provincia_region_pais.csv': InversionID,
    'indicadores_contexto_y_sicytar.csv': IndicadoresContexto,
    'rrhh_sicytar_agregado_provincia_region_pais.csv': RRHHsicytar,
    'rrhh_ract_esid.csv': RRHHract,
    'esid_inversion_sectores_provincia_region_pais.csv': InversionEmpresariaSector,
    'expo_nivel_tecnologico_provincia_region_pais.csv': ExportacionNivelTecnologico,
    'expo_por_provincia_top5.csv': ExportacionTop5,
    'expo_tecno_destino.csv': ExportacionTecnologicaDestino,
    'percepcion_final.csv': PercepcionSocial,
    'listado_unidades_de_id.csv': UnidadID,
    'equipos_ssnn_provincia_region_pais.csv': EquipamientoSSNN,
    'inversion_y_articulos_por_investigador_provincia_region_pais.csv': InversionArticulosPorInvestigador,
    'proyectos_pfi.csv': ProyectoPFI,
    'productos_provincia_region_pais_renaprod.csv': ProductoCientifico,
    'patentes_desagregadas_ipc_provincia_region_pais.csv': Patente,
    'proyectos_provincia_region_pais_renaprod.csv': Proyecto,
}

class Command(BaseCommand):
    help = 'Carga los datos de los archivos CSV de CTI en la base de datos'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando la carga de datos de CTI...'))
        data_dir = os.path.join(settings.BASE_DIR, '..', 'data')

        # Carga especial para Provincia, ya que es una dependencia para otros
        self._cargar_provincias(data_dir)
        self._cargar_indicadores_contexto(data_dir)
        self._cargar_unidadesID(data_dir)
        self._cargar_proyectosPFI(data_dir)

        # Carga del resto de los modelos
        for filename, model in ARCHIVOS_A_CARGAR.items():
            if model == Provincia:  # Ya se cargó
                continue
            if model == IndicadoresContexto:  # Ya se cargó
                continue
            if model == UnidadID:   # Ya se cargó
                continue
            if model == ProyectoPFI:  # Ya se cargó
                continue

            try:
                self.stdout.write(f'Cargando datos para el modelo {model.__name__} desde {filename}...')
                df = pd.read_csv(os.path.join(data_dir, filename), sep=';')
                df = df.where(pd.notna(df), None)  # Reemplazar NaN por None

                # Borramos los datos existentes para evitar duplicados
                model.objects.all().delete()

                # Creamos los objetos en memoria
                objetos_a_crear = []
                for _, row in df.iterrows():
                    # Mapeo de columnas CSV a campos del modelo
                    data_dict = {field.name: row.get(field.db_column or field.name) for field in model._meta.fields if not field.primary_key}

                    objetos_a_crear.append(model(**data_dict))
                
                # Inserción en bloque para máxima eficiencia
                model.objects.bulk_create(objetos_a_crear, batch_size=1000)
                self.stdout.write(self.style.SUCCESS(f'Se cargaron {len(objetos_a_crear)} registros para {model.__name__}.'))

            except FileNotFoundError:
                self.stdout.write(self.style.ERROR(f'Error: No se encontró el archivo {filename}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Ocurrió un error al cargar {model.__name__}: {e}'))

        self.stdout.write(self.style.SUCCESS('Proceso de carga de datos finalizado.'))

    def _cargar_provincias(self, data_dir):
        try:
            self.stdout.write('Cargando datos de Provincias...')
            df = pd.read_csv(os.path.join(data_dir, 'ref_provincia.csv'), sep=';')
            df = df.where(pd.notna(df), None)

            for _, row in df.iterrows():
                Provincia.objects.update_or_create(
                    provincia_id=row['provincia_id'],
                    defaults={
                        'nombre': row['provincia'],
                        'codigo_indec': row.get('codigo_indec'),
                        'region_mincyt': row.get('region_mincyt'),
                        'region_iso': row.get('region_iso'),
                        'region_cofecyt': row.get('region_cofecyt'),
                    }
                )
            self.stdout.write(self.style.SUCCESS(f'Se procesaron {len(df)} registros para Provincia.'))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR('Error: No se encontró el archivo ref_provincia.csv'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ocurrió un error al cargar Provincias: {e}'))

    def _cargar_indicadores_contexto(self, data_dir):
        self.stdout.write('--- Procesando: indicadores_contexto_y_sicytar.csv (Carga Especial) ---')
        try:
            df = pd.read_csv(os.path.join(data_dir, 'indicadores_contexto_y_sicytar.csv'), sep=';')
            df = df.where(pd.notna(df), None)
            
            for _, row in df.iterrows():
                # SOLUCIÓN: Leemos explícitamente el 'id' del CSV y lo pasamos al modelo
                IndicadoresContexto.objects.update_or_create(
                    id=row['id'],  # ID para esta tabla
                    defaults={
                        'provincia': row.get('provincia'),
                        'poblacion_censo_2022': row.get('poblacion_censo_2022'),
                        'superficie': row.get('superficie'),
                        'vab_cepal_2022': row.get('vab_cepal_2022'),
                        'tasas_actividad_eph_3trim_2024': row.get('tasas_actividad_eph_3trim_2024'),
                        'tasa_empleo_3trim_2024': row.get('tasa_empleo_3trim_2024'),
                        'tasa_desocupacion_eph_3trim_2024': row.get('tasa_desocupacion_eph_3trim_2024'),
                        'cant_empresas_sipa_2022': row.get('cant_empresas_sipa_2022'),
                        'trabajo_registrado_sipa_2024': row.get('trabajo_registrado_sipa_2024'),
                        'exportaciones_millones_uss_opex_2023': row.get('exportaciones_millones_uss_opex_2023'),
                        'pea_miles_eph_3trim_2024': row.get('pea_miles_eph_3trim_2024'),
                        'pea_miles_censo_2022': row.get('pea_miles_censo_2022'),
                        'becario_id': row.get('becario_id'),
                        'docente': row.get('docente'),
                        'investigador': row.get('investigador'),
                        'otro_personal': row.get('otro_personal'),
                        'tasa_inv_millon_hab': row.get('tasa_inv_millon_hab'),
                        'tasa_inv_1000_pea': row.get('tasa_inv_1000_pea'),
                    }
                )
            self.stdout.write(self.style.SUCCESS(f'OK: Se procesaron {len(df)} registros para IndicadoresContexto.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'ERROR cargando IndicadoresContexto: {e}'))

    def _cargar_unidadesID(self, data_dir):
        try:
            self.stdout.write('Cargando datos de Unidades ID...')
            df = pd.read_csv(os.path.join(data_dir, 'listado_unidades_de_id.csv'), sep=';')
            df = df.where(pd.notna(df), None)

            for _, row in df.iterrows():
                UnidadID.objects.update_or_create(
                    organizacion_id=row['organizacion_id'],
                    defaults={
                        'organizacion': row['organizacion'],
                        'nivel_1': row.get('nivel_1'),
                        'provincia': row.get('provincia'),
                    }
                )
            self.stdout.write(self.style.SUCCESS(f'Se procesaron {len(df)} registros para Unidades ID.'))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR('Error: No se encontró el archivo listado_unidades_de_id.csv'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ocurrió un error al cargar Unidades ID: {e}'))

    def _cargar_proyectosPFI(self, data_dir):
        try:
            self.stdout.write('Cargando datos de Proyectos PFI...')
            df = pd.read_csv(os.path.join(data_dir, 'proyectos_pfi.csv'), sep=';')
            df = df.where(pd.notna(df), None)

            for _, row in df.iterrows():
                ProyectoPFI.objects.update_or_create(
                    id_pfi=row['id_pfi'],
                    defaults={
                        'anio': row['anio'],
                        'cupo': row.get('cupo'),
                        'region_cofecyt': row.get('region_cofecyt'),
                        'provincia': row.get('provincia'),
                        'tema': row.get('tema'),
                        'sector': row.get('sector'),
                        'vertical': row.get('vertical'),
                        'tecnologias': row.get('tecnologias'),
                        'vertical_tecnologia': row.get('vertical_tecnologia'),
                    }
                )
            self.stdout.write(self.style.SUCCESS(f'Se procesaron {len(df)} registros para Proyectos PFI.'))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR('Error: No se encontró el archivo proyectos_pfi.csv'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ocurrió un error al cargar Proyectos PFI: {e}'))