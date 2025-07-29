import logging
import json
import pandas as pd
import numpy as np
import plotly.express as px
from jinja2 import Environment, meta
from .models import Informe
from datos_fuente.data_handler import ejecutar_consulta_parametrizada


logger = logging.getLogger(__name__)


class NumpyEncoder(json.JSONEncoder):
    """
    Clase personalizada para enseñarle a `json.dumps` cómo manejar
    objetos que no son nativos de JSON, como los arrays de NumPy.
    """
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()  # Convierte el array de NumPy a una lista de Python
        return json.JSONEncoder.default(self, obj)


class GeneradorInforme:
    """ Gestiona la generación de una instancia de un informe específico. """
    def __init__(self, informe_id: int):
        try:
            self.informe = Informe.objects.get(pk=informe_id)
            logger.info(f"Generador inicializado para el informe: '{self.informe.nombre}'")
        except Informe.DoesNotExist:
            logger.error(f"Error: El informe con ID {informe_id} no existe.")
            raise ValueError(f"El informe con ID {informe_id} no existe.")

    def _renderizar_config_dinamica(self, config: dict, params: dict) -> dict:
        env = Environment()
        rendered_config = {}
        for key, value in config.items():
            if isinstance(value, str) and "{{" in value:
                template = env.from_string(value)
                variables = meta.find_undeclared_variables(env.parse(value))
                contexto = {k: v for k, v in params.items() if k in variables}
                rendered_config[key] = template.render(contexto)
            elif isinstance(value, dict):
                rendered_config[key] = self._renderizar_config_dinamica(value, params)
            else:
                rendered_config[key] = value
        return rendered_config

    def _procesar_kpi(self, df: pd.DataFrame, config: dict) -> str:
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

    def _procesar_tabla(self, df: pd.DataFrame, config: dict, params: dict) -> dict:
        if df.empty:
            return None

        if config.get("pivot"):
            try:
                pivot_config = config.get("pivot")
                df_pivot = df.pivot_table(
                    index=pivot_config.get("index"), columns=pivot_config.get("columns"),
                    values=pivot_config.get("values"), fill_value=""
                ).reset_index()
                headers = list(df_pivot.columns)
                cell_values = [df_pivot[col].to_list() for col in headers]

            except Exception as e:
                logger.error(f"No se pudo procesar la tabla. Error: {e}")
                return None
            else:
                # Renderizar tabla simple
                try:
                    headers_config = config.get("headers", {})
                    cells_config = config.get("cells", {})
                    headers = list(df[headers_config["values"]]) if headers_config else df.columns.tolist()
                    cell_values = list(df[cells_config["values"]]) if cells_config else df.values.tolist()

                except Exception as e:
                    logger.error(f"No se pudo procesar la tabla.'. Error: {e}")
                    return None

            layout_config = self._renderizar_config_dinamica(config.get("layout", {}), params)

            # Devolvemos un diccionario con los datos y el layout
            return {
                "data": [{'type': 'table', 'header': {'values': headers}, 'cells': {'values': cell_values}}],
                "layout": layout_config
            }

    def _procesar_grafico(self, df: pd.DataFrame, config: dict, params: dict, subtipo: str) -> dict:
        if df.empty:
            return None
        mapping = self._renderizar_config_dinamica(config.get("plot_mapping", {}), params)
        layout_config = self._renderizar_config_dinamica(config.get("layout", {}), params)

        """
        plot_cols = [v for v in mapping.values() if isinstance(v, str) and v]
        if not all(col in df.columns for col in plot_cols): return None
        df.dropna(subset=plot_cols, inplace=True)

        numeric_keys = ['x', 'y', 'values']
        for key, col_name in mapping.items():
            if key in numeric_keys and isinstance(col_name, str) and col_name in df.columns:
                df[col_name] = pd.to_numeric(df[col_name], errors='coerce')
        df.dropna(subset=plot_cols, inplace=True)
        if df.empty:
            return None
        """

        traces = []
        if subtipo == 'line':
            if 'color' in mapping:
                color_col = mapping.get('color')
                for name, group in df.groupby(color_col):
                    traces.append({
                        'x': group[mapping['x']].to_list(),
                        'y': group[mapping['y']].to_list(),
                        'name': name,
                        'type': 'scatter',
                        'mode': 'lines+markers'
                    })
            else:
                traces.append({
                    'x': df[mapping['x']].to_list(),
                    'y': df[mapping['y']].to_list(),
                    'type': 'scatter',
                    'mode': 'lines+markers'
                })
        elif subtipo == 'bar':
            if 'color' in mapping:
                color_col = mapping.get('color')
                for name, group in df.groupby(color_col):
                    traces.append({
                        'x': group[mapping['x']].to_list(),
                        'y': group[mapping['y']].to_list(),
                        'name': name,
                        'type': 'bar'
                    })
            else:
                traces.append({
                    'x': df[mapping['x']].to_list(),
                    'y': df[mapping['y']].to_list(),
                    'type': 'bar'
                })
        elif subtipo == 'barh':
            if 'color' in mapping:
                color_col = mapping.get('color')
                for name, group in df.groupby(color_col):
                    traces.append({
                        'x': group[mapping['y']].to_list(),
                        'y': group[mapping['x']].to_list(),
                        'name': name,
                        'orientation': 'h',
                        'type': 'bar'
                    })
            else:
                traces.append({
                    'x': df[mapping['x']].to_list(),
                    'y': df[mapping['y']].to_list(),
                    'orientation': 'h',
                    'type': 'bar'
                })
        elif subtipo == 'pie':
            traces.append({
                'labels': df[mapping['labels']].to_list(),
                'values': df[mapping['values']].to_list(),
                'type': 'pie',
                'hole': mapping.get("hole", 0)
            })
        elif subtipo == 'treemap':
            fig = px.treemap(
                    df,
                    path=[df.iloc[:, 0]],
                    values=df[mapping['values']]
                )
            fig.update_traces(root_color="white")
            fig.update_layout(margin=dict(t=50, l=25, r=25, b=25))
            traces = []
            for trace in fig.data:
                # 2. Convertimos cada traza a un diccionario y extraemos sus datos como listas
                #    Esto fuerza la conversión de cualquier formato interno (como bdata) a una lista simple.
                trace_dict = {
                    'type': trace.type,
                    'labels': list(getattr(trace, 'labels', [])),
                    'values': list(getattr(trace, 'values', [])),
                    'parents': list(getattr(trace, 'parents', [])),
                }
                traces.append(trace_dict)

        return {"data": traces, "layout": layout_config}

    def generar(self, params: dict):
        """
        Ejecuta el flujo completo para generar el informe.
        Ahora también renderiza los nombres de los componentes.
        """
        logger.info(f"Iniciando generación de informe '{self.informe.nombre}' con parámetros: {params}")
        resultados_componentes = []
        composicion = self.informe.informecomposicion_set.order_by('orden')

        # Creamos un único entorno de Jinja para reutilizarlo
        env = Environment()

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
                resultado_final = self._procesar_tabla(df_datos, config, params)
            elif tipo == "GRAFICO":
                resultado_final = self._procesar_grafico(df_datos, config, params, subtipo)

            nombre_template = env.from_string(componente.nombre)
            nombre_renderizado = nombre_template.render(params)

            resultados_componentes.append({
                'nombre': nombre_renderizado,
                'orden': item_composicion.orden,
                'tipo': tipo,
                'subtipo': subtipo,
                'resultado': resultado_final
            })

        logger.info("Generación de informe finalizada.")
        return resultados_componentes
