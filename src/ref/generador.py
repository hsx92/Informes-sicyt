import logging
import pandas as pd
import plotly.express as px
from jinja2 import Environment, meta

from .models import Informe
from datos_fuente.data_handler import ejecutar_consulta_parametrizada

logger = logging.getLogger(__name__)


class GeneradorInforme:
    """ Gestiona la generación de una instancia de un informe específico. """
    def __init__(self, informe_id: int):
        try:
            self.informe = Informe.objects.get(pk=informe_id)
            logger.info(f"Generador inicializado para el informe: '{self.informe.nombre}'")
        except Informe.DoesNotExist:
            logger.error(f"Error: El informe con ID {informe_id} no existe.")
            raise ValueError(f"El informe con ID {informe_id} no existe.")

    def _procesar_kpi(self, df: pd.DataFrame, config: dict) -> str:
        """ Extrae y formatea un valor único de un DataFrame para un KPI. """
        if df.empty:
            return "N/A"
        
        # Extraemos el primer valor de la primera fila/columna
        valor = df.iloc[0, 0]
        
        # Aplicamos formato si está definido en la configuración
        formato = config.get('format', 'raw')
        sufijo = config.get('suffix', '')

        if formato == 'int':
            return f"{int(valor):,}{sufijo}".replace(",", ".")
        if formato == 'float':
            return f"{valor:,.2f}{sufijo}".replace(",", "X").replace(".", ",").replace("X", ".")
            
        return f"{valor}{sufijo}"

    def _procesar_grafico(self, df: pd.DataFrame, config: dict, params: dict, tipo_grafico: str) -> str:
        """
        Genera un gráfico con Plotly. Inspecciona dinámicamente las plantillas
        tanto en el layout como en el mapeo de ejes.
        """
        if df.empty: return None

        mapping = config.get("plot_mapping", {}).copy()
        layout_config = config.get("layout", {}).copy()
        env = Environment()
        
        # --- INICIO DE LA LÓGICA DE RENDERIZADO ---

        # 1. Renderizado dinámico del mapeo de ejes
        rendered_mapping = {}
        for key, template_str in mapping.items():
            if isinstance(template_str, str) and "{{" in template_str:
                ast = env.parse(template_str)
                variables = meta.find_undeclared_variables(ast)
                contexto = {k: v for k, v in params.items() if k in variables}
                rendered_mapping[key] = env.from_string(template_str).render(contexto)
            else:
                rendered_mapping[key] = template_str  # Usar el valor tal cual si no es una plantilla

        # 2. Renderizado dinámico del título del layout
        title_config = layout_config.get("title", {})
        template_str_titulo = title_config.get("text", "")
        if isinstance(template_str_titulo, str) and "{{" in template_str_titulo:
            ast = env.parse(template_str_titulo)
            variables = meta.find_undeclared_variables(ast)
            contexto = {k: v for k, v in params.items() if k in variables}
            title_config["text"] = env.from_string(template_str_titulo).render(contexto)
            layout_config["title"] = title_config
        
        # 3. Limpieza de datos
        x_col, y_col = rendered_mapping.get("x"), rendered_mapping.get("y")

        if tipo_grafico == "GRAFICO.barh":
            # Para barras horizontales, solo el eje X es numérico
            df[x_col] = pd.to_numeric(df[x_col], errors='coerce')
            df.dropna(subset=[x_col], inplace=True) # Validamos solo la columna numérica
        
        elif tipo_grafico == "GRAFICO.line":
            # Para líneas, ambos ejes suelen ser numéricos
            df[x_col] = pd.to_numeric(df[x_col], errors='coerce')
            df[y_col] = pd.to_numeric(df[y_col], errors='coerce')
            df.dropna(subset=[x_col, y_col], inplace=True)
        
        # Verificamos si el DataFrame sigue teniendo datos después de la limpieza
        print(df.head())  # Para depuración, muestra las primeras filas del DataFrame
        logger.info(f"DataFrame después de limpieza: {df.shape[0]} filas, {df.shape[1]} columnas")

        if df.empty:
            logger.warning("DataFrame vacío después de la limpieza. No se puede generar gráfico.")
            return None

        # Selección de la función de gráfico correcta
        if tipo_grafico == "GRAFICO.barh":
            fig = px.bar(df, x=x_col, y=y_col, orientation='h', text_auto=True)
        elif tipo_grafico == "GRAFICO.line":
            fig = px.line(df, x=x_col, y=y_col)

        fig.update_layout(**layout_config)
        return fig.to_json()

    def generar(self, params: dict):
        """ Ejecuta el flujo completo para generar el informe. """
        logger.info(f"Iniciando generación de informe '{self.informe.nombre}' con parámetros: {params}")
        resultados_componentes = []
        
        composicion = self.informe.informecomposicion_set.order_by('orden')
        
        for item_composicion in composicion:
            componente = item_composicion.componente
            logger.info(f"Procesando componente (Orden {item_composicion.orden}): '{componente.nombre}'")

            if not componente.plantilla_sql:
                logger.info("Componente sin plantilla SQL. Se omite.")
                continue

            df_datos = ejecutar_consulta_parametrizada(
                plantilla_sql=componente.plantilla_sql,
                params=params
            )
            
            # Combinamos la configuración base con los overrides del informe
            config = componente.config_visualizacion
            config.update(item_composicion.config_override)

            resultado_final = None
            tipo = componente.tipo_componente
            
            if tipo == "KPI":
                resultado_final = self._procesar_kpi(df_datos, config)
            elif "GRAFICO" in tipo:
                resultado_final = self._procesar_grafico(df_datos, config, params, tipo)
            
            print(f"\n--- Resultado Final para: {componente.nombre} ---")
            print(resultado_final)
            print("---------------------------------------------------\n")

            resultados_componentes.append({
                'nombre': componente.nombre,
                'orden': item_composicion.orden,
                'tipo': tipo,
                'resultado': resultado_final
            })

        logger.info("Generación de informe finalizada.")
        return resultados_componentes
