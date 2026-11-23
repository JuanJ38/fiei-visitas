"""
Módulo de Machine Learning de FIEI Visitas.

Reproduce lo que hace el notebook de Colab (secciones 7, 8, 9, 13 y 14):

  * Convierte las visitas en conteos por fecha, hora y piso.
  * Entrena dos Random Forest: HORA (visitas por hora) y DIA (visitas por día).
  * Responde consultas: dada una fecha y un piso, devuelve la cantidad esperada.

Los modelos se guardan en la carpeta `modelos/` como archivos .joblib.
Si faltan, o si fueron creados con otra versión de scikit-learn, se vuelven
a entrenar solos (tarda unos segundos).
"""

import json
import threading
from datetime import timedelta

import joblib
import numpy as np
import pandas as pd
import sklearn
from django.conf import settings
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from .models import Visita

# Variables de entrada (X). La salida (y) es la columna `visitas`.
FEATURES = ["dia_semana", "mes", "dia_mes", "dia_anio", "hora", "piso"]
MODALIDADES = ("HORA", "DIA")
PISOS_MODELO = [0, 1, 2, 3, 4, 5]  # 0 = toda la FIEI (suma de los cinco pisos)
SEED = 2026

_cache = {}
_candado = threading.Lock()


# --------------------------------------------------------------------------
# Preparación de datos (sección 7 del notebook)
# --------------------------------------------------------------------------
def cargar_historial():
    """Lee las visitas guardadas en la base de datos y devuelve un DataFrame."""
    filas = list(Visita.objects.values_list("ingreso", "piso"))
    df = pd.DataFrame(filas, columns=["ingreso", "piso"])
    if df.empty:
        return df
    df["ingreso"] = pd.to_datetime(df["ingreso"])
    df["piso"] = df["piso"].astype(int)
    df["fecha"] = df["ingreso"].dt.normalize()
    df["hora"] = df["ingreso"].dt.hour
    return df


def crear_agregados(data, modalidad, fechas_modelo):
    """
    Cuenta visitas por (fecha, hora, piso). Agrega el piso 0 (toda la FIEI)
    y rellena con 0 las combinaciones donde no hubo visitas.
    """
    aux = data[["fecha", "hora", "piso"]].copy()
    if modalidad == "DIA":
        aux["hora"] = -1
    totales = aux.copy()
    totales["piso"] = 0
    union = pd.concat([aux, totales], ignore_index=True)
    conteos = union.groupby(["fecha", "hora", "piso"]).size().rename("visitas")

    franjas = range(24) if modalidad == "HORA" else [-1]
    idx = pd.MultiIndex.from_product(
        [fechas_modelo, franjas, PISOS_MODELO], names=["fecha", "hora", "piso"]
    )
    tabla = conteos.reindex(idx, fill_value=0).reset_index()
    tabla["dia_semana"] = tabla["fecha"].dt.dayofweek
    tabla["mes"] = tabla["fecha"].dt.month
    tabla["dia_mes"] = tabla["fecha"].dt.day
    tabla["dia_anio"] = tabla["fecha"].dt.dayofyear
    return tabla


def _nuevo_modelo():
    # Misma configuración que el notebook (sección 9).
    return RandomForestRegressor(
        n_estimators=150, min_samples_leaf=2, random_state=42, n_jobs=-1
    )


def _ruta(modalidad):
    return settings.MODELOS_DIR / f"random_forest_{modalidad.lower()}.joblib"


# --------------------------------------------------------------------------
# Evaluación (secciones 8 y 9 del notebook)
# --------------------------------------------------------------------------
def evaluar(tabla, con_serie=False):
    """
    Entrena con el 80 % de los días y prueba con el 20 % final (sección 8 y 9),
    y compara con la línea base de promedios (sección 10).
    """
    dias = sorted(tabla["fecha"].unique())
    n_prueba = max(1, int(np.floor(len(dias) * 0.20)))
    fecha_corte = pd.Timestamp(dias[-n_prueba])
    train = tabla[tabla["fecha"] < fecha_corte]
    test = tabla[tabla["fecha"] >= fecha_corte]

    modelo = _nuevo_modelo()
    modelo.fit(train[FEATURES], train["visitas"])
    pred = np.maximum(0, modelo.predict(test[FEATURES]))

    # Línea base: promedio histórico por piso, hora y día de la semana
    claves = ["piso", "hora", "dia_semana"]
    medias = train.groupby(claves)["visitas"].mean().rename("base")
    temp = test.join(medias, on=claves)
    temp["base"] = temp["base"].fillna(train["visitas"].mean())

    resultado = {
        "fecha_corte": fecha_corte.strftime("%Y-%m-%d"),
        "entrenamiento_hasta": (fecha_corte - timedelta(days=1)).strftime("%Y-%m-%d"),
        "dias_entrenamiento": len(dias) - n_prueba,
        "dias_prueba": n_prueba,
        "muestras_prueba": int(len(test)),
        "MAE": round(float(mean_absolute_error(test["visitas"], pred)), 3),
        "RMSE": round(float(np.sqrt(mean_squared_error(test["visitas"], pred))), 3),
        "R2": round(float(r2_score(test["visitas"], pred)), 3),
        "MAE_base": round(float(mean_absolute_error(temp["visitas"], temp["base"])), 3),
    }
    if con_serie:
        # Visitas reales vs. predichas de toda la FIEI (piso 0) en los días de prueba
        comp = test.assign(prediccion=pred)
        comp = comp[comp["piso"] == 0].sort_values("fecha")
        resultado["serie"] = {
            "fechas": [f.strftime("%d/%m") for f in comp["fecha"]],
            "observado": [int(v) for v in comp["visitas"]],
            "prediccion": [round(float(v), 1) for v in comp["prediccion"]],
        }
    return resultado


def _ruta_evaluacion():
    return settings.MODELOS_DIR / "evaluacion.json"


def calcular_evaluacion(df=None, fechas_modelo=None):
    """Evalúa los dos modelos y guarda el resultado en modelos/evaluacion.json."""
    if df is None:
        df = cargar_historial()
    if df.empty:
        raise ValueError("No hay visitas en la base de datos.")
    if fechas_modelo is None:
        fechas_modelo = pd.date_range(df["fecha"].min(), df["fecha"].max(), freq="D")
    paquete = {
        "visitas_usadas": int(len(df)),
        "desde": df["fecha"].min().strftime("%d/%m/%Y"),
        "hasta": df["fecha"].max().strftime("%d/%m/%Y"),
        "modelos": {},
    }
    for modalidad in MODALIDADES:
        tabla = crear_agregados(df, modalidad, fechas_modelo)
        paquete["modelos"][modalidad] = evaluar(tabla, con_serie=(modalidad == "DIA"))
    settings.MODELOS_DIR.mkdir(parents=True, exist_ok=True)
    _ruta_evaluacion().write_text(
        json.dumps(paquete, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    return paquete


def obtener_evaluacion():
    """
    Devuelve la evaluación guardada. Si todavía no existe, la calcula una vez
    (tarda unos segundos) y la guarda. Solo se actualiza al ejecutar
    `python manage.py entrenar_modelos --evaluar`.
    """
    ruta = _ruta_evaluacion()
    if ruta.exists():
        try:
            return json.loads(ruta.read_text(encoding="utf-8"))
        except Exception:
            pass
    return calcular_evaluacion()


NOMBRES_VARIABLES = {
    "dia_semana": "Día de la semana",
    "mes": "Mes",
    "dia_mes": "Día del mes",
    "dia_anio": "Día del año",
    "hora": "Hora",
    "piso": "Piso",
}


def importancias():
    """Importancia de cada variable en los modelos finales (sección 12)."""
    resultado = {}
    for modalidad in MODALIDADES:
        valores = obtener_modelo(modalidad).feature_importances_
        filas = sorted(zip(FEATURES, valores), key=lambda p: p[1], reverse=True)
        resultado[modalidad] = [
            {"variable": NOMBRES_VARIABLES[f], "porcentaje": round(float(v) * 100, 1)}
            for f, v in filas
        ]
    return resultado


# --------------------------------------------------------------------------
# Entrenamiento y carga de modelos
# --------------------------------------------------------------------------
def entrenar_modelos(con_evaluacion=False):
    """
    Entrena los dos modelos con TODO el histórico de la base de datos y los
    guarda en `modelos/`. Devuelve las métricas si `con_evaluacion=True`.
    """
    df = cargar_historial()
    if df.empty:
        raise ValueError(
            "No hay visitas en la base de datos. Ejecuta primero: "
            "python manage.py cargar_datos"
        )
    fechas_modelo = pd.date_range(df["fecha"].min(), df["fecha"].max(), freq="D")
    settings.MODELOS_DIR.mkdir(parents=True, exist_ok=True)

    metricas = {}
    for modalidad in MODALIDADES:
        tabla = crear_agregados(df, modalidad, fechas_modelo)
        modelo = _nuevo_modelo()
        modelo.fit(tabla[FEATURES], tabla["visitas"])
        joblib.dump(
            {
                "modelo": modelo,
                "features": FEATURES,
                "modalidad": modalidad,
                "seed": SEED,
                "sklearn_version": sklearn.__version__,
            },
            _ruta(modalidad),
            compress=3,
        )
        modelo.n_jobs = 1  # consultas pequeñas: un solo proceso es más rápido
        _cache[modalidad] = modelo
    if con_evaluacion:
        metricas = calcular_evaluacion(df, fechas_modelo)["modelos"]
    return metricas


def _cargar_de_disco(modalidad):
    ruta = _ruta(modalidad)
    if not ruta.exists():
        return None
    try:
        paquete = joblib.load(ruta)
        version = paquete.get("sklearn_version")
        if version and version != sklearn.__version__:
            return None  # creado con otra versión: mejor reentrenar
        modelo = paquete["modelo"]
        modelo.n_jobs = 1
        return modelo
    except Exception:
        return None


def obtener_modelo(modalidad):
    """Devuelve el modelo (desde memoria, disco, o lo entrena si hace falta)."""
    if modalidad not in MODALIDADES:
        raise ValueError("Modalidad no válida. Usa DIA o HORA.")
    if modalidad in _cache:
        return _cache[modalidad]
    with _candado:
        if modalidad not in _cache:
            modelo = _cargar_de_disco(modalidad)
            if modelo is None:
                entrenar_modelos()
            else:
                _cache[modalidad] = modelo
    return _cache[modalidad]


# --------------------------------------------------------------------------
# Consultas (secciones 13 y 14 del notebook)
# --------------------------------------------------------------------------
def vector_fecha(fecha, hora, piso):
    """Convierte una fecha en los 6 números que entiende el modelo."""
    f = pd.Timestamp(fecha)
    return [f.dayofweek, f.month, f.day, f.dayofyear, hora, piso]


def consultar(fecha, piso=0, modalidad="DIA"):
    """
    Cantidad esperada de visitas.
      modalidad 'DIA'  -> una fila (total del día)
      modalidad 'HORA' -> 24 filas (una por hora)
    piso 0 = toda la FIEI.
    """
    modalidad = modalidad.upper()
    if piso not in PISOS_MODELO:
        raise ValueError("Piso no válido: 0 a 5.")
    franjas = list(range(24)) if modalidad == "HORA" else [-1]
    X = pd.DataFrame(
        [vector_fecha(fecha, h, piso) for h in franjas], columns=FEATURES
    )
    yhat = np.round(np.maximum(0, obtener_modelo(modalidad).predict(X)), 1)
    f = pd.Timestamp(fecha).date()
    return [
        {"fecha": f, "hora": h, "piso": piso, "visitas": float(v)}
        for h, v in zip(franjas, yhat)
    ]


def pronostico_dias(fecha_inicio, piso=0, dias=7):
    """Pronóstico diario para `dias` fechas consecutivas (modalidad DIA)."""
    inicio = pd.Timestamp(fecha_inicio).date()
    fechas = [inicio + timedelta(days=i) for i in range(dias)]
    X = pd.DataFrame(
        [vector_fecha(f, -1, piso) for f in fechas], columns=FEATURES
    )
    yhat = np.round(np.maximum(0, obtener_modelo("DIA").predict(X)), 1)
    return [
        {"fecha": f, "piso": piso, "visitas": float(v)} for f, v in zip(fechas, yhat)
    ]
