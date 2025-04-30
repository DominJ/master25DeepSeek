"""
Programa de Monitorización del Sistema Eléctrico Español

Este programa obtiene y visualiza datos en tiempo real del estado
de la red eléctrica nacional usando la API de Red Eléctrica de España.
"""

import requests
import matplotlib.pyplot as plt
from datetime import datetime
import logging
from typing import Dict, Any

# Configuración básica
API_BASE_URL = "https://api.esios.ree.es"
HEADERS = {
    "Accept": "application/json; application/vnd.esios-api-v2+json",
    "Content-Type": "application/json",
    "Host": "api.esios.ree.es"
}

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def obtener_token() -> str:
    """
    Obtiene el token de autenticación para la API de REE.
    
    Returns:
        str: Token de autenticación.
        
    Raises:
        SystemExit: Si no se puede obtener el token.
    """
    try:
        # EN LA PRÁCTICA DEBES OBTENER ESTO DE VARIABLES DE ENTORNO O CONFIG
        token = "TU_TOKEN_DE_API_AQUI"  # Reemplazar con token real
        if not token or token == "TU_TOKEN_DE_API_AQUI":
            raise ValueError("Token no configurado")
        return token
    except Exception as e:
        logger.error(f"Error obteniendo token: {e}")
        raise SystemExit("No se pudo obtener el token de API")


def hacer_peticion_api(endpoint: str, token: str) -> Dict[str, Any]:
    """
    Realiza una petición a la API de REE.
    
    Args:
        endpoint (str): Endpoint de la API a consultar.
        token (str): Token de autenticación.
        
    Returns:
        dict: Respuesta JSON de la API.
        
    Raises:
        SystemExit: Si la petición falla.
    """
    try:
        headers = HEADERS.copy()
        headers["Authorization"] = f"Token token={token}"
        
        response = requests.get(
            f"{API_BASE_URL}{endpoint}",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error en petición API: {e}")
        raise SystemExit("Error al conectarse con la API de REE")


def obtener_datos_red_electrica(token: str) -> Dict[str, Any]:
    """
    Obtiene los datos actuales del sistema eléctrico.
    
    Args:
        token (str): Token de autenticación.
        
    Returns:
        dict: Datos estructurados del sistema eléctrico.
    """
    endpoint = "/indicators/1014"  # Ejemplo, ajustar al endpoint correcto
    datos = hacer_peticion_api(endpoint, token)
    
    # Procesamiento básico de datos (ajustar según respuesta real de la API)
    datos_procesados = {
        "fecha_actualizacion": datos.get("datetime", datetime.now().isoformat()),
        "demanda_actual": datos.get("value", 0),
        "porcentaje_renovable": datos.get("renewable_percentage", 0),
        "desglose_generacion": {
            "nuclear": datos.get("nuclear", 0),
            "eolica": datos.get("wind", 0),
            "solar": datos.get("solar", 0),
            "hidraulica": datos.get("hydro", 0),
            "cogeneracion": datos.get("co-generation", 0),
            "carbon": datos.get("coal", 0),
            "ciclo_combinado": datos.get("combined-cycle", 0),
            "otras": datos.get("other", 0)
        }
    }
    
    return datos_procesados


def generar_grafico_demanda(datos: Dict[str, Any]) -> None:
    """
    Genera un gráfico de la demanda eléctrica actual.
    
    Args:
        datos (dict): Datos del sistema eléctrico.
    """
    plt.figure(figsize=(10, 6))
    plt.bar(["Demanda Actual"], [datos["demanda_actual"]], color='blue')
    plt.title(f"Demanda Eléctrica Actual: {datos['demanda_actual']} MW")
    plt.ylabel("MW")
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()


def generar_grafico_generacion(datos: Dict[str, Any]) -> None:
    """
    Genera un gráfico circular del mix de generación.
    
    Args:
        datos (dict): Datos del sistema eléctrico.
    """
    desglose = datos["desglose_generacion"]
    labels = list(desglose.keys())
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
    plt.title("Mix de Generación Eléctrica")
    plt.axis('equal')
    plt.tight_layout()


def mostrar_datos_consola(datos: Dict[str, Any]) -> None:
    """
    Muestra los datos principales en la consola.
    
    Args:
        datos (dict): Datos del sistema eléctrico.
    """
    print("\n" + "="*50)
    print(f"ESTADO DE LA RED ELÉCTRICA - {datos['fecha_actualizacion']}")
    print("="*50)
    print(f"\n• Demanda actual: {datos['demanda_actual']} MW")
    print(f"• Porcentaje renovable: {datos['porcentaje_renovable']}%")
    
    print("\nMix de generación:")
    for fuente, valor in datos["desglose_generacion"].items():
        print(f"  - {fuente.capitalize()}: {valor} MW")


def ejecutar_monitorizacion() -> None:
    """
    Función principal que ejecuta todo el proceso de monitorización.
    """
    try:
        logger.info("Iniciando monitorización de la red eléctrica...")
        
        # 1. Autenticación
        token = obtener_token()
        
        # 2. Obtener datos
        datos = obtener_datos_red_electrica(token)
        
        # 3. Mostrar en consola
        mostrar_datos_consola(datos)
        
        # 4. Generar visualizaciones
        generar_grafico_demanda(datos)
        generar_grafico_generacion(datos)
        
        # 5. Mostrar gráficos
        plt.show()
        
        logger.info("Monitorización completada con éxito")
        
    except Exception as e:
        logger.error(f"Error en la ejecución: {e}")
        raise SystemExit("El programa terminó con errores")


if __name__ == "__main__":
    ejecutar_monitorizacion()