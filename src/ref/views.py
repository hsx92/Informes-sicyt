from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.template.loader import render_to_string
from datos_fuente.models import Provincia
# from .models import Informe
from .generador import GeneradorInforme
import logging

logger = logging.getLogger(__name__)


def generar_informe_api(request, informe_id):
    """
    Vista de API para generar un informe, devuelve una página HTML
    con las visualizaciones renderizadas.
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    # 1. Obtenemos y validamos los parámetros
    provincia_id_str = request.GET.get('provincia_id')
    anio_str = request.GET.get('anio')
    if not all([provincia_id_str, anio_str]):
        return HttpResponseBadRequest("Los parámetros 'provincia_id' y 'anio' son requeridos.")
    try:
        provincia_id = int(provincia_id_str)
        anio = int(anio_str)
        provincia = Provincia.objects.get(pk=provincia_id)
    except (ValueError, TypeError):
        return HttpResponseBadRequest("Los parámetros deben ser números enteros.")
    except Provincia.DoesNotExist:
        return JsonResponse({'error': f'La provincia con ID {provincia_id} no existe.'}, status=404)

    # 2. Creamos y ejecutamos el generador
    try:
        generador = GeneradorInforme(informe_id=informe_id)
        params = {
            'provincia_id': provincia.provincia_id,
            'provincia_nombre': provincia.nombre,
            'anio': anio
        }
        resultados = generador.generar(params=params)

        if resultados is None:
            return JsonResponse({'error': 'No se pudo generar el informe.'}, status=500)

        # --- INICIO DE LA NUEVA LÓGICA DE RENDERIZADO ---

        # 3. Preparamos el contexto para la plantilla
        contexto = {
            'informe': generador.informe,
            'resultados': resultados,  # Pasamos el JSON como string
            'params': params,
        }

        # 4. Renderizamos el HTML y lo devolvemos en un HttpResponse
        html_string = render_to_string('ref/informe_vista.html', contexto)
        return HttpResponse(html_string)
        # --- FIN DE LA NUEVA LÓGICA ---

    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=404)
    except Exception as e:
        logger.error(f"Error inesperado al generar el informe: {e}", exc_info=True)
        return JsonResponse({'error': 'Ocurrió un error interno en el servidor.'}, status=500)
