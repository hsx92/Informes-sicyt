import pandas as pd
from jinja2 import Template
from sqlalchemy import create_engine, text
from django.conf import settings
import logging

# Configuración de un logger para este módulo
logger = logging.getLogger(__name__)

def ejecutar_consulta_parametrizada(plantilla_sql: str, params: dict) -> pd.DataFrame:
    """
    Toma una plantilla SQL y un diccionario de parámetros, la renderiza
    y ejecuta la consulta contra la base de datos, devolviendo un DataFrame de Pandas.

    Args:
        plantilla_sql: Un string con la consulta SQL que contiene placeholders de Jinja2.
        params: Un diccionario con los valores para reemplazar los placeholders.

    Returns:
        Un DataFrame de Pandas con el resultado de la consulta.
        Retorna un DataFrame vacío si ocurre un error.
    """
    logger.info("Iniciando ejecución de consulta parametrizada...")
    
    # 1. Conexión a la base de datos usando SQLAlchemy
    # Se toman las credenciales desde el settings.py de Django para mantener una única fuente de verdad.
    try:
        db_settings = settings.DATABASES['default']
        engine_url = (
            f"postgresql+psycopg2://{db_settings['USER']}:{db_settings['PASSWORD']}"
            f"@{db_settings['HOST']}:{db_settings['PORT']}/{db_settings['NAME']}"
        )
        engine = create_engine(engine_url)
    except Exception as e:
        logger.error(f"Error al configurar el motor de SQLAlchemy: {e}")
        return pd.DataFrame()

    # 2. Renderizado de la plantilla SQL con Jinja2 para inyectar los parámetros de forma segura
    try:
        template = Template(plantilla_sql)
        sql_renderizado = template.render(params)
        logger.info(f"SQL Renderizado: \n{sql_renderizado}")
    except Exception as e:
        logger.error(f"Error al renderizar la plantilla SQL con Jinja2: {e}")
        return pd.DataFrame()

    # 3. Ejecución de la consulta usando Pandas y el motor de SQLAlchemy
    try:
        with engine.connect() as connection:
            df = pd.read_sql_query(sql=text(sql_renderizado), con=connection)
        logger.info(f"Consulta exitosa. Se obtuvieron {len(df)} filas y {len(df.columns)} columnas.")
        return df
    except Exception as e:
        logger.error(f"Error al ejecutar la consulta SQL con Pandas: {e}")
        return pd.DataFrame()