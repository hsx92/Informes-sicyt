import logging
from .models import Informe
from datos_fuente.data_handler import ejecutar_consulta_parametrizada

# Configuración de un logger para este módulo
logger = logging.getLogger(__name__)


class GeneradorInforme:
    """
    Gestiona la generación de una instancia de un informe específico.
    """
    def __init__(self, informe_id: int):
        """
        Inicializa el generador para un informe específico.

        Args:
            informe_id: El ID del objeto Informe que se desea generar.
        """
        try:
            self.informe = Informe.objects.get(pk=informe_id)
            logger.info(f"Generador inicializado para el informe: '{self.informe.nombre}'")
        except Informe.DoesNotExist:
            logger.error(f"No se pudo inicializar el Generador: El informe con ID {informe_id} no existe.")
            raise ValueError(f"El informe con ID {informe_id} no existe.")

    def generar(self, params: dict):
        """
        Ejecuta el flujo completo para generar el informe.

        Args:
            params: Un diccionario con los parámetros para la ejecución del informe 
                    (ej: {'provincia_id': 90, 'provincia_nombre': 'Tucumán'}).
        """
        logger.info(f"Iniciando generación de informe '{self.informe.nombre}' con parámetros: {params}")

        resultados_componentes = []
        
        # 1. Obtenemos la lista ordenada de componentes para el informe
        composicion = self.informe.informecomposicion_set.order_by('orden')
        
        if not composicion.exists():
            logger.warning(f"El informe '{self.informe.nombre}' no tiene componentes definidos.")
            return None

        # 2. Iteramos sobre cada componente para procesarlo
        for item_composicion in composicion:
            componente = item_composicion.componente
            logger.info(f"Procesando componente (Orden {item_composicion.orden}): '{componente.nombre}'")

            # 3. Ejecutamos la consulta SQL del componente usando nuestro data_handler
            if componente.plantilla_sql:
                df_datos = ejecutar_consulta_parametrizada(
                    plantilla_sql=componente.plantilla_sql,
                    params=params
                )
                
                print(f"\n--- Datos para el componente: {componente.nombre} ---")
                print(df_datos.to_string())
                print("---------------------------------------------------\n")

                resultados_componentes.append({
                    'nombre': componente.nombre,
                    'orden': item_composicion.orden,
                    'datos': df_datos
                })
            else:
                logger.info(f"El componente '{componente.nombre}' no tiene plantilla SQL. Se omite la carga de datos.")

        logger.info("Generación de informe finalizada.")
        return resultados_componentes