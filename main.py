"""
Programa de Monitorización del Sistema Eléctrico Español
Versión con visualización de gráficos corregida
"""

import requests
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import logging
from typing import Dict, Any, List
import matplotlib.dates as mdates
import random
import colorsys

# Configuración de matplotlib para mostrar correctamente los gráficos
plt.switch_backend('TkAgg')  # O 'Qt5Agg' si usas PyQt
plt.style.use('ggplot')

# Configuración básica
API_BASE_URL = "https://apidatos.ree.es"
HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def hacer_peticion_api(endpoint: str, params: Dict[str, str] = None) -> Dict[str, Any]:
    """Realiza una petición a la API pública de REE."""
    try:
        response = requests.get(
            f"{API_BASE_URL}{endpoint}",
            headers=HEADERS,
            params=params,
            timeout=15
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error en petición API: {e}")
        raise SystemExit(f"Error al conectarse con la API de REE: {str(e)}")


def obtener_datos_generacion(fecha_inicio: str, fecha_fin: str) -> List[Dict[str, Any]]:
    """Obtiene los datos de generación eléctrica para un rango de fechas."""
    endpoint = "/es/datos/generacion/estructura-generacion"
    params = {
        "start_date": f"{fecha_inicio}T00:00",
        "end_date": f"{fecha_fin}T23:59",
        "time_trunc": "day"
    }
    
    datos = hacer_peticion_api(endpoint, params)
    
    datos_procesados = []
    for item in datos.get("included", []):
        tipo_generacion = item.get("type", "")
        valores = item.get("attributes", {}).get("values", [])
        
        for valor in valores:
            fecha = valor.get("datetime", "")
            valor_mw = valor.get("value", 0)
            
            entrada_existente = next((x for x in datos_procesados if x["fecha"] == fecha), None)
            if not entrada_existente:
                entrada_existente = {
                    "fecha": datetime.strptime(fecha[:10], "%Y-%m-%d"),
                    "total_generacion": 0,
                    "desglose_generacion": {}
                }
                datos_procesados.append(entrada_existente)
            
            entrada_existente["desglose_generacion"][tipo_generacion] = valor_mw
            entrada_existente["total_generacion"] += valor_mw
    
    # Ordenar por fecha
    datos_procesados.sort(key=lambda x: x["fecha"])
    return datos_procesados


def obtener_datos_demanda(fecha_inicio: str, fecha_fin: str) -> List[Dict[str, Any]]:
    """Obtiene los datos de demanda eléctrica para un rango de fechas."""
    endpoint = "/es/datos/demanda/evolucion"
    params = {
        "start_date": f"{fecha_inicio}T00:00",
        "end_date": f"{fecha_fin}T23:59",
        "time_trunc": "day"
    }
    
    datos = hacer_peticion_api(endpoint, params)
    
    datos_procesados = []
    for item in datos.get("included", []):
        valores = item.get("attributes", {}).get("values", [])
        
        for valor in valores:
            datos_procesados.append({
                "fecha": datetime.strptime(valor.get("datetime", "")[:10], "%Y-%m-%d"),
                "demanda": float(valor.get("value", 0)),
                "unidad": "MW"
            })
    
    # Ordenar por fecha
    datos_procesados.sort(key=lambda x: x["fecha"])
    return datos_procesados

def obtener_tipos_generacion_existentes(datos: List[Dict[str, Any]]) -> List[str]:
    """
    Filtra los tipos de generación eléctrica que realmente existen en los datos.
    
    Args:
        datos: Lista de diccionarios con los datos de generación por fecha
        tipos_posibles: Lista de todos los posibles tipos de generación
        
    Returns:
        Lista de tipos de generación que están presentes en los datos
    """
    tipos_existentes = []
    
    # Verificamos si este tipo aparece en al menos un día de datos
    for dia in datos:
        for key, value in dia["desglose_generacion"].items():
            if key not in tipos_existentes:
                tipos_existentes.append(key)
                break  # Pasamos al siguiente tipo
    
    return tipos_existentes

def crear_estructura_datos_apilados(datos: List[Dict[str, Any]], 
                                   tipos_generacion: List[str]) -> Dict[str, List[float]]:
    """
    Crea un diccionario para almacenar los datos apilados del gráfico.
    
    Args:
        datos: Lista de diccionarios con los datos de generación por fecha
        tipos_generacion: Tipos de generación a incluir
        
    Returns:
        Diccionario donde cada clave es un tipo de generación y el valor
        es una lista con los valores para cada fecha
    """
    # Inicializamos con listas vacías para cada tipo
    datos_apilados = {tipo: [] for tipo in tipos_generacion}
    
    # Para cada día, añadimos los valores correspondientes
    for dia in datos:
        for key, value in dia["desglose_generacion"].items():
            for tipo in tipos_generacion:
                if key == tipo: 
                    datos_apilados[tipo].append(value)
                else:
                    datos_apilados[tipo].append(0)
    
    return datos_apilados

def generar_diccionario_colores_distintivos(tipos_generacion):
    """
    Genera colores más distintivos usando el espacio de color HSV.
    
    Args:
        tipos_generacion (list): Lista de strings con los tipos de generación
        
    Returns:
        dict: Diccionario con colores más variados y distinguibles
    """
    colores = {}
    n = len(tipos_generacion)
    
    for i, tipo in enumerate(tipos_generacion):
        # Usamos el espacio HSV para obtener colores bien distribuidos
        hue = i / n  # Distribuimos el matiz uniformemente
        saturation = 0.7 + random.random() * 0.3  # Saturación alta
        value = 0.5 + random.random() * 0.5  # Valor medio-alto
        
        # Convertimos HSV a RGB y luego a hexadecimal
        r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
        color = "#{:02x}{:02x}{:02x}".format(
            int(r * 255),
            int(g * 255),
            int(b * 255)
        )
        colores[tipo] = color
    
    return colores

def generar_grafico_generacion(datos: List[Dict[str, Any]], fecha_inicio: str, fecha_fin: str, ax: plt.Axes) -> None:
    """Genera un gráfico de barras apiladas del mix de generación."""
    if not datos:
        raise ValueError("No hay datos de generación para mostrar")
    
    # 1. Extraemos las fechas de los datos
    fechas = [d["fecha"] for d in datos]
    
    # 1. Obtenemos solo los tipos que existen en los datos
    tipos_existentes = obtener_tipos_generacion_existentes(datos)
    
    # 2. Creamos la estructura de datos apilados
    datos_apilados = crear_estructura_datos_apilados(datos, tipos_existentes)

    # Colores para cada tipo de generación
    colors = generar_diccionario_colores_distintivos(tipos_existentes)
    
    # Generamos el gráfico apilado
    bottom = None
    for tipo in datos_apilados.keys():
        ax.bar(
            fechas,
            datos_apilados[tipo],
            label=tipo.capitalize(),
            bottom=bottom,
            color=colors.get(tipo, '#7f7f7f'),
            width=0.8  # Ancho de las barras
        )
        bottom = [sum(x) for x in zip(bottom or [0]*len(fechas), datos_apilados[tipo])]
    
    # Configuración del gráfico
    ax.set_title(f"Mix de Generación Eléctrica\n{fecha_inicio} a {fecha_fin}", pad=20)
    ax.set_xlabel("Fecha") 
    ax.set_ylabel("MW")
    
    # Formatear fechas en el eje X
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.DayLocator())
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
    
    # Añadir leyenda fuera del gráfico
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # Añadir grid
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Ajustar márgenes
    ax.margins(x=0.05)


def generar_grafico_demanda(datos: List[Dict[str, Any]], fecha_inicio: str, fecha_fin: str, ax: plt.Axes) -> None:
    """Genera un gráfico de línea de la evolución de la demanda."""
    if not datos:
        raise ValueError("No hay datos de demanda para mostrar")
    
    fechas = [d["fecha"] for d in datos]
    demanda = [d["demanda"] for d in datos]
    
    # Gráfico de línea con marcadores
    ax.plot(fechas, demanda, marker='o', linestyle='-', linewidth=2, 
            markersize=6, color='#1f77b4', label='Demanda')
    
    # Configuración del gráfico
    ax.set_title(f"Evolución de la Demanda Eléctrica\n{fecha_inicio} a {fecha_fin}", pad=20)
    ax.set_xlabel("Fecha")
    ax.set_ylabel("MW")
    
    # Formatear fechas en el eje X
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.DayLocator())
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
    
    # Añadir grid
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # Añadir leyenda
    ax.legend()
    
    # Ajustar márgenes
    ax.margins(x=0.05)


def mostrar_datos_consola(datos_gen: List[Dict[str, Any]], datos_dem: List[Dict[str, Any]]) -> None:
    """Muestra los datos principales en la consola."""
    if not datos_gen or not datos_dem:
        print("No hay datos suficientes para mostrar")
        return
    
    print("\n" + "="*60)
    print("RESUMEN DEL SISTEMA ELÉCTRICO ESPAÑOL")
    print("="*60)
    
    # Mostrar últimos datos disponibles
    ultimo_gen = datos_gen[-1]
    ultimo_dem = datos_dem[-1]
    
    print(f"\nÚltimos datos disponibles: {ultimo_gen['fecha'].strftime('%Y-%m-%d')}")
    print(f"\n• Demanda: {ultimo_dem['demanda']:.2f} {ultimo_dem['unidad']}")
    print(f"• Generación total: {ultimo_gen['total_generacion']:.2f} MW")
    
    print("\nDesglose de generación:")
    for tipo, valor in sorted(ultimo_gen["desglose_generacion"].items(), key=lambda x: x[1], reverse=True):
        porcentaje = (valor / ultimo_gen["total_generacion"]) * 100
        print(f"  - {tipo.capitalize():<15}: {valor:>8.2f} MW ({porcentaje:.1f}%)")


def ejecutar_monitorizacion() -> None:
    """Función principal que ejecuta todo el proceso de monitorización."""
    try:
        logger.info("Iniciando monitorización de la red eléctrica...")
        
        # Configurar rango de fechas (últimos 7 días por defecto)
        fecha_fin = datetime.now().strftime("%Y-%m-%d")
        fecha_inicio = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        # 1. Obtener datos
        logger.info(f"Obteniendo datos desde {fecha_inicio} hasta {fecha_fin}...")
        datos_generacion = obtener_datos_generacion(fecha_inicio, fecha_fin)
        datos_demanda = obtener_datos_demanda(fecha_inicio, fecha_fin)
        
        if not datos_generacion or not datos_demanda:
            raise ValueError("No se pudieron obtener datos completos")
        
        # 2. Mostrar en consola
        mostrar_datos_consola(datos_generacion, datos_demanda)
        
        # 3. Crear figura con dos subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12))
        
        # 4. Generar gráficos
        generar_grafico_demanda(datos_demanda, fecha_inicio, fecha_fin, ax1)
        generar_grafico_generacion(datos_generacion, fecha_inicio, fecha_fin, ax2)
        
        # 5. Ajustar layout y mostrar
        plt.subplots_adjust(hspace=0.5)  # Espacio entre subplots
        plt.tight_layout()
        plt.show()
        
        logger.info("Monitorización completada con éxito")
        
    except Exception as e:
        logger.error(f"Error en la ejecución: {e}")
        raise SystemExit(f"El programa terminó con errores: {str(e)}")

if __name__ == "__main__":
    ejecutar_monitorizacion()