import logging
import os
from django.conf import settings
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
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

    # --- FUNCIONES AUXILIARES (HELPERS) ---

    def _renderizar_config_dinamica(self, config: dict, params: dict) -> dict:
        """
        Renderiza cualquier plantilla Jinja2 encontrada en un diccionario de configuración.
        """
        env = Environment()
        rendered_config = {}
        for key, value in config.items():
            if isinstance(value, str) and "{{" in value:
                template = env.from_string(value)
                variables = meta.find_undeclared_variables(env.parse(value))
                contexto = {k: v for k, v in params.items() if k in variables}
                rendered_config[key] = template.render(contexto)
            elif isinstance(value, dict):  # Para configuraciones anidadas como 'layout.title'
                rendered_config[key] = self._renderizar_config_dinamica(value, params)
            else:
                rendered_config[key] = value
        return rendered_config

    def _guardar_visualizacion_html(self, fig, layout_config, nombre_componente):
        """Función auxiliar para guardar cualquier figura de Plotly como HTML."""
        try:
            output_dir = os.path.join(settings.BASE_DIR, '..', 'output')
            os.makedirs(output_dir, exist_ok=True)
            titulo = layout_config.get("title", {}).get("text", nombre_componente)
            nombre_sanitizado = "".join(c for c in titulo if c.isalnum() or c in (' ', '_')).rstrip()
            nombre_archivo = f"{nombre_sanitizado.replace(' ', '_')}.html"
            ruta_completa = os.path.join(output_dir, nombre_archivo)
            fig.write_html(ruta_completa)
            logger.info(f"Visualización guardada exitosamente en: {ruta_completa}")
        except Exception as e:
            logger.error(f"No se pudo guardar la visualización como HTML: {e}")

    # --- FUNCIONES DE PROCESAMIENTO POR TIPO ---

    def _procesar_kpi(self, df: pd.DataFrame, config: dict) -> str:
        """ Procesa un DataFrame para generar un KPI.
        Extrae el primer valor del DataFrame, aplica formato y devuelve una cadena.
        Si el DataFrame está vacío o el primer valor es NaN, devuelve "N/A".
        """

        if df.empty or pd.isna(df.iloc[0, 0]):
            return "N/A"
        valor = df.iloc[0, 0]
        formato = config.get('format', 'raw')
        sufijo = config.get('suffix', '')
        if formato == 'int':
            return f"{int(float(valor)):,}{sufijo}".replace(",", ".")
        if formato == 'float':
            return f"{float(valor):,.2f}{sufijo}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{valor}{sufijo}"

    def _procesar_tabla(self, df: pd.DataFrame, config: dict, params: dict, nombre_componente: str) -> str:
        """ Procesa un DataFrame para generar una tabla visualizable.
        Si la configuración incluye un pivot, se aplica un pivot_table.
        Si no, se renderiza una tabla simple con los headers y celdas especificadas.
        """

        if df.empty:
            return None

        if "pivot" in config:
            pivot_config = config.get("pivot")
            try:
                df_pivot = df.pivot_table(
                    index=pivot_config.get("index"), columns=pivot_config.get("columns"),
                    values=pivot_config.get("values"), fill_value=""
                ).reset_index()
                headers = list(df_pivot.columns)
                cell_values = [df_pivot[col] for col in headers]
            except Exception as e:
                logger.error(f"No se pudo procesar la tabla para '{nombre_componente}'. Error: {e}")
                return None
        else:
            # Renderizar tabla simple
            try:
                print(df.head())  # Debug: Verificar el contenido del DataFrame
                headers_config = config.get("headers", {})
                cells_config = config.get("cells", {})
                headers = list(df[headers_config["values"]]) if headers_config else df.columns.tolist()
                cell_values = list(df[cells_config["values"]]) if cells_config else df.values.tolist()
                print(f"Headers: {headers}, Cell Values: {cell_values}")  # Debug: Verificar headers y celdas
            except Exception as e:
                logger.error(f"No se pudo procesar la tabla para '{nombre_componente}'. Error: {e}")
                return None

        layout_config = self._renderizar_config_dinamica(config.get("layout", {}), params)

        fig = go.Figure(data=[go.Table(header=dict(values=headers), cells=dict(values=cell_values))])
        fig.update_layout(**layout_config)

        return pio.to_html(fig, full_html=False, include_plotlyjs=False)

    def _procesar_grafico(self, df: pd.DataFrame, config: dict, params: dict, subtipo: str, nombre_componente: str) -> str:
        """ Procesa un DataFrame para generar un gráfico según el tipo especificado.
        Renderiza la configuración dinámica, limpia los datos y crea el gráfico.
        Si el DataFrame está vacío, devuelve None.
        """

        if df.empty:
            return None

        # PASO 1: Renderizar toda la configuración primero
        mapping = self._renderizar_config_dinamica(config.get("plot_mapping", {}), params)
        layout_config = self._renderizar_config_dinamica(config.get("layout", {}), params)

        # PASO 2: Limpieza de datos
        """plot_cols = [v for v in mapping.values() if v]

        for col in ['values', 'hole']:
            if col in mapping and mapping[col] in df.columns:
                df[mapping[col]] = pd.to_numeric(df[mapping[col]], errors='coerce')

        df.dropna(subset=plot_cols, inplace=True)
        if df.empty:
            return None"""

        # PASO 3: Creación del gráfico
        fig = go.Figure()

        if subtipo == 'line':
            if mapping.get('color'):
                for name, group in df.groupby(mapping['color']):
                    fig.add_trace(
                        go.Scatter(
                            x=group[mapping['x']],
                            y=group[mapping['y']],
                            name=name,
                            mode='lines+markers'
                        )
                    )
            else:
                fig.add_trace(
                    go.Scatter(
                        x=df[mapping['x']],
                        y=df[mapping['y']],
                        mode='lines+markers')
                    )

        elif subtipo == 'bar':
            fig.add_trace(
                go.Bar(
                    x=df[mapping['x']],
                    y=df[mapping['y']],
                    text=df[mapping['y']],
                    textposition='auto'
                )
            )

        elif subtipo == 'barh':
            fig.add_trace(
                go.Bar(
                    x=df[mapping['x']],
                    y=df[mapping['y']],
                    orientation='h',
                    text=df[mapping['x']],
                    textposition='auto'
                )
            )

        elif subtipo == 'pie':
            fig.add_trace(
                go.Pie(
                    labels=df[mapping['labels']],
                    values=df[mapping['values']],
                    hole=mapping.get('hole', 0.0),
                )
            )

        elif subtipo == 'treemap':
            treefig = px.treemap(
                    df,
                    path=[df.iloc[:, 0]],
                    values=df[mapping['values']]
                )
            treefig.update_traces(root_color="white")
            treefig.update_layout(**layout_config)
            treefig.update_layout(margin=dict(t=50, l=25, r=25, b=25))
            self._guardar_visualizacion_html(treefig, layout_config, nombre_componente)
            return treefig.to_json()

        fig.update_layout(**layout_config)
        return pio.to_html(fig, full_html=False, include_plotlyjs=False)

    def generar(self, params: dict):
        """ Ejecuta el flujo completo para generar el informe. """
        logger.info(f"Iniciando generación de informe '{self.informe.nombre}' con parámetros: {params}")
        resultados_componentes = []
        composicion = self.informe.informecomposicion_set.order_by('orden')

        for item_composicion in composicion:
            componente = item_composicion.componente
            logger.info(f"Procesando componente (Orden {item_composicion.orden}): '{componente.nombre}'")

            if not componente.plantilla_sql:
                continue
            df_datos = ejecutar_consulta_parametrizada(plantilla_sql=componente.plantilla_sql, params=params)
            config = componente.config_visualizacion.copy()

            if item_composicion.config_override:
                config.update(item_composicion.config_override)

            resultado_final = None
            tipo = componente.tipo_componente
            subtipo = componente.tipo_grafico

            if tipo == "KPI":
                resultado_final = self._procesar_kpi(df_datos, config)
            elif tipo == "TABLA":
                resultado_final = self._procesar_tabla(df_datos, config, params, componente.nombre)
            elif tipo == "GRAFICO":
                resultado_final = self._procesar_grafico(df_datos, config, params, subtipo, componente.nombre)

            print(f"\n--- Resultado Final para: {componente.nombre} ---")
            print(resultado_final)
            print("---------------------------------------------------\n")

            resultados_componentes.append({
                'nombre': componente.nombre, 'orden': item_composicion.orden,
                'tipo': tipo, 'subtipo': subtipo, 'resultado': resultado_final
            })

        logger.info("Generación de informe finalizada.")
        return resultados_componentes
