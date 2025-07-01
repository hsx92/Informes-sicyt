import logging
import os
from django.conf import settings
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
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
    
    def _procesar_tabla(self, df: pd.DataFrame, config: dict, params: dict) -> str:
        """
        Procesa un DataFrame, lo pivotea según la configuración y lo convierte
        en un objeto go.Table, renderizando dinámicamente el título.
        """
        if df.empty:
            return None

        pivot_config = config.get("pivot")
        if not pivot_config:
            logger.error("La configuración de pivote es necesaria para el componente de tabla.")
            return None
        
        try:
            df_pivot = df.pivot_table(
                index=pivot_config.get("index"),
                columns=pivot_config.get("columns"),
                values=pivot_config.get("values"),
                fill_value="",
            ).reset_index()
        except Exception as e:
            logger.error(f"No se pudo pivotar la tabla. Error: {e}")
            return None

        # Preparamos los datos para go.Table
        headers = list(df_pivot.columns)
        cell_values = [df_pivot[col] for col in headers]

        # --- LÓGICA DE RENDERIZADO DE TÍTULO ---
        layout_config = config.get("layout", {}).copy()
        env = Environment()
        
        title_config = layout_config.get("title", {})
        template_str_titulo = title_config.get("text", "")
        if isinstance(template_str_titulo, str) and "{{" in template_str_titulo:
            ast = env.parse(template_str_titulo)
            variables_requeridas = meta.find_undeclared_variables(ast)
            contexto_renderizado = {k: v for k, v in params.items() if k in variables_requeridas}
            title_config["text"] = env.from_string(template_str_titulo).render(contexto_renderizado)
            layout_config["title"] = title_config
        # --- FIN DE LA NUEVA LÓGICA ---

        # Creamos la figura de Plotly
        fig = go.Figure(data=[go.Table(
            header=dict(values=headers,
                        fill_color='paleturquoise',
                        align='left'),
            cells=dict(values=cell_values,
                       fill_color='lavender',
                       align='left'))
        ])
        
        fig.update_layout(**layout_config)

        # --- GUARDAR COMO HTML ---
        try:
            # Construimos una ruta segura al directorio de salida
            output_dir = os.path.join(settings.BASE_DIR, '..', 'output')
            os.makedirs(output_dir, exist_ok=True) # Crea el directorio si no existe
            
            # Generamos un nombre de archivo descriptivo
            nombre_archivo = f"{title_config['text']}.html"
            ruta_completa = os.path.join(output_dir, nombre_archivo)
            
            fig.write_html(ruta_completa)
            logger.info(f"Gráfico guardado exitosamente en: {ruta_completa}")

        except Exception as e:
            logger.error(f"No se pudo guardar el gráfico como HTML: {e}")

        return fig.to_json()

    def _procesar_grafico(self, df: pd.DataFrame, config: dict, params: dict, tipo_grafico: str) -> str:
        """
        Genera un gráfico con Plotly. Inspecciona dinámicamente las plantillas
        tanto en el layout como en el mapeo de ejes.
        """
        if df.empty: return None

        mapping = config.get("plot_mapping", {}).copy()
        layout_config = config.get("layout", {}).copy()
        env = Environment()

        # Renderizado dinámico del mapeo de ejes
        rendered_mapping = {}
        for key, template_str in mapping.items():
            if isinstance(template_str, str) and "{{" in template_str:
                ast = env.parse(template_str)
                variables = meta.find_undeclared_variables(ast)
                contexto = {k: v for k, v in params.items() if k in variables}
                rendered_mapping[key] = env.from_string(template_str).render(contexto)
            else:
                rendered_mapping[key] = template_str  # Usar el valor tal cual si no es una plantilla

        # Renderizado dinámico del título del layout
        title_config = layout_config.get("title", {})
        template_str_titulo = title_config.get("text", "")
        if isinstance(template_str_titulo, str) and "{{" in template_str_titulo:
            ast = env.parse(template_str_titulo)
            variables = meta.find_undeclared_variables(ast)
            contexto = {k: v for k, v in params.items() if k in variables}
            title_config["text"] = env.from_string(template_str_titulo).render(contexto)
            layout_config["title"] = title_config

        # Validación de columnas requeridas
        x_col, y_col, color_col = rendered_mapping.get("x"), rendered_mapping.get("y"), rendered_mapping.get("color")

        # Limpieza de datos
        if tipo_grafico == "barh":
            # Para barras horizontales, solo el eje X es numérico
            df[x_col] = pd.to_numeric(df[x_col], errors='coerce')
            df.dropna(subset=[x_col], inplace=True) # Validamos solo la columna numérica

        elif tipo_grafico == "line":
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
        
        # Creamos la figura de Plotly
        fig = go.Figure() # Creamos una figura vacía

        # Selección de la función de gráfico correcta
        if tipo_grafico == "line":
            # Para gráficos de líneas, agrupamos por la columna de color para crear una traza por cada serie
            for name, group in df.groupby(color_col):
                fig.add_trace(
                    go.Scatter(
                        x=group[x_col],
                        y=group[y_col],
                        name=name,
                        mode='lines+markers'
                    )
                )

        elif tipo_grafico == "barh":
            # Para barras horizontales, añadimos una única traza
            fig.add_trace(
                go.Bar(
                    x=df[x_col],
                    y=df[y_col],
                    orientation='h',
                    text=df[x_col],
                    textposition='auto'
                )
            )

        elif tipo_grafico == "pie":
            fig.add_trace(
                go.Pie(
                    labels=df[x_col],
                    values=df[y_col],
                    hole=layout_config.get("hole", 0)
                )
            )

        fig.update_layout(**layout_config)

        # --- GUARDAR COMO HTML ---
        try:
            # Construimos una ruta segura al directorio de salida
            output_dir = os.path.join(settings.BASE_DIR, '..', 'output')
            os.makedirs(output_dir, exist_ok=True) # Crea el directorio si no existe
            
            # Generamos un nombre de archivo descriptivo
            nombre_archivo = f"{title_config['text']}_{tipo_grafico}.html"
            ruta_completa = os.path.join(output_dir, nombre_archivo)
            
            fig.write_html(ruta_completa)
            logger.info(f"Gráfico guardado exitosamente en: {ruta_completa}")

        except Exception as e:
            logger.error(f"No se pudo guardar el gráfico como HTML: {e}")

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
            tipo_grafico = componente.tipo_grafico
            
            if tipo == "KPI":
                resultado_final = self._procesar_kpi(df_datos, config)
            elif tipo == "GRAFICO":
                resultado_final = self._procesar_grafico(df_datos, config, params, tipo_grafico)
            elif tipo == "TABLA":
                resultado_final = self._procesar_tabla(df_datos, config, params)

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
