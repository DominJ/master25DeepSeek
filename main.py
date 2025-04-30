"""
Programa de Monitorización del Sistema Eléctrico Español (Versión sin autenticación)

Este programa obtiene y visualiza datos públicos del estado
de la red eléctrica nacional usando la API abierta de REE.
"""

import requests
import matplotlib.pyplot as plt
from datetime import datetime
import logging
from typing import Dict, Any

# Configuración básica
API_BASE_URL = "https://apidatos.ree.es"
HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def hacer_peticion_api(endpoint: str) -> Dict[str, Any]:
    """
    Realiza una petición a la API pública de REE.
    
    Args:
        endpoint (str): Endpoint de la API a consultar.
        
    Returns:
        dict: Respuesta JSON de la API.
        
    Raises:
        SystemExit: Si la petición falla.
    """
    try:
        response = requests.get(
            f"{API_BASE_URL}{endpoint}",
            headers=HEADERS,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error en petición API: {e}")
        raise SystemExit("Error al conectarse con la API de REE")


def obtener_datos_generacion() -> Dict[str, Any]:
    """
    Obtiene los datos actuales de generación eléctrica.
    
    Returns:
        dict: Datos estructurados de generación.
    """
    endpoint = "/es/datos/generacion/estructura-generacion"
    datos = hacer_peticion_api(endpoint)
    
    # Procesamiento de datos (ajustar según respuesta real)
    datos_procesados = {
        "fecha_actualizacion": datos.get("datetime", datetime.now().isoformat()),
        "total_generacion": datos.get("total", 0),
        "desglose_generacion": {
            "nuclear": datos.get("nuclear", 0),
            "eolica": datos.get("eolica", 0),
            "solar": datos.get("solar", 0),
            "hidraulica": datos.get("hidraulica", 0),
            "cogeneracion": datos.get("cogeneracion", 0),
            "carbon": datos.get("carbon", 0),
            "ciclo_combinado": datos.get("ciclo_combinado", 0),
            "otras": datos.get("otras", 0)
        }
    }
    
    return datos_procesados


def obtener_datos_demanda() -> Dict[str, Any]:
    """
    Obtiene los datos actuales de demanda eléctrica.
    
    Returns:
        dict: Datos estructurados de demanda.
    """
    endpoint = "/es/datos/demanda/evolucion"
    datos = hacer_peticion_api(endpoint)
    
    datos_procesados = {
        "fecha_actualizacion": datos.get("datetime", datetime.now().isoformat()),
        "demanda_actual": datos.get("value", 0),
        "unidad": "MW"
    }
    
    return datos_procesados


def generar_grafico_generacion(datos: Dict[str, Any]) -> None:
    """
    Genera un gráfico circular del mix de generación.
    """
    desglose = datos["desglose_generacion"]
    labels = [k.capitalize() for k in desglose.keys()]
    sizes = list(desglose.values())
    colors = [
        '#FF9999', '#66B3FF', '#99FF99', '#FFCC99',
        '#c2c2f0', '#ffb3e6', '#FFD700', '#C0C0C0'
    ]
    
    plt.figure(figsize=(10, 6))
    plt.pie(
        sizes,
        labels=labels,
        colors=colors,
        autopct='%1.1f%%',
        startangle=90,
        wedgeprops={'edgecolor': 'white', 'linewidth': 1}
    )
    plt.title(f"Mix de Generación Eléctrica\nTotal: {datos['total_generacion']} MW")
    plt.axis('equal')
    plt.tight_layout()


def mostrar_datos_consola(datos_gen: Dict[str, Any], datos_dem: Dict[str, Any]) -> None:
    """
    Muestra los datos principales en la consola.
    """
    print("\n" + "="*50)
    print(f"ESTADO DE LA RED ELÉCTRICA - {datos_gen['fecha_actualizacion']}")
    print("="*50)
    print(f"\n• Demanda actual: {datos_dem['demanda_actual']} {datos_dem['unidad']}")
    print(f"• Generación total: {datos_gen['total_generacion']} MW")
    
    print("\nMix de generación:")
    for fuente, valor in datos_gen["desglose_generacion"].items():
        print(f"  - {fuente.capitalize()}: {valor} MW")


def ejecutar_monitorizacion() -> None:
    """
    Función principal que ejecuta todo el proceso de monitorización.
    """
    try:
        logger.info("Iniciando monitorización de la red eléctrica...")
        
        # 1. Obtener datos
        datos_generacion = obtener_datos_generacion()
        datos_demanda = obtener_datos_demanda()
        
        # 2. Mostrar en consola
        mostrar_datos_consola(datos_generacion, datos_demanda)
        
        # 3. Generar visualizaciones
        generar_grafico_generacion(datos_generacion)
        
        # 4. Mostrar gráficos
        plt.show()
        
        logger.info("Monitorización completada con éxito")
        
    except Exception as e:
        logger.error(f"Error en la ejecución: {e}")
        raise SystemExit("El programa terminó con errores")


if __name__ == "__main__":
    ejecutar_monitorizacion()