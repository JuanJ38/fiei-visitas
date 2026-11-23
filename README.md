# FIEI Visitas · aplicación web (Django)

Predicción de la cantidad de visitantes de la FIEI por piso con Random Forest.
Es la parte web del proyecto del Grupo 02 de Ingeniería del Conocimiento (UNFV).
Usa los **mismos datos y modelos que el notebook de Colab**: por eso los resultados coinciden
con la presentación (MAE 0,541 y 4,280; pronóstico del 18 al 24/11: 109, 114, 116,8, 34, 32,6, 109,6, 109,7).

## Pantallas

| Pantalla | Dirección | Qué hace |
|---|---|---|
| Dashboard | `/` | Total de visitas, cinco pisos, gráfico por piso y evolución diaria |
| Registrar | `/registrar/` | Formulario: piso, destino, fecha/hora, tipo, motivo y cantidad |
| Historial | `/historial/` | Lista de visitas con filtro por piso y paginación |
| Afluencia | `/afluencia/` | Fecha + piso (o toda la FIEI) + modalidad (día u hora) → gráfico y tabla |
| Admin | `/admin/` | Opcional (hay que crear un usuario con `createsuperuser`) |

Al abrir **Afluencia** se muestra de entrada el ejemplo del PDF (18/11/2026, toda la FIEI, 7 días).

## Qué contiene la carpeta

```
manage.py                 arranque de Django
requirements.txt          librerías necesarias
db.sqlite3                base de datos ya cargada con las 16 500 visitas
datos/                    CSV que genera el notebook (visitas_fiei_16500_sinteticas.csv)
modelos/                  random_forest_hora.joblib y random_forest_dia.joblib (del notebook)
config/                   configuración de Django (settings.py, urls.py, wsgi.py)
visitas/                  la aplicación
  models.py               tabla Visita
  ml.py                   Random Forest: preparar datos, entrenar, consultar (secciones 7, 9, 13 y 14 del notebook)
  views.py                las cuatro pantallas
  forms.py                formularios de registro y de afluencia
  management/commands/    cargar_datos.py y entrenar_modelos.py
  templates/ y static/    HTML, CSS y Chart.js (los gráficos funcionan sin internet)
```

---

## 1. Probarlo en tu PC (PyCharm o terminal)

Necesitas Python 3.10 o superior. SQLite ya viene incluido con Python.

```bash
# Dentro de la carpeta del proyecto (donde está manage.py)
python -m venv venv

# Activar el entorno:
venv\Scripts\activate            # Windows
# source venv/bin/activate       # Linux / Mac

pip install -r requirements.txt
python manage.py runserver
```

Abre <http://127.0.0.1:8000>. No hace falta correr `migrate`: la base ya viene lista.

En PyCharm: *File → Open* la carpeta, crea el intérprete con el `venv`, instala `requirements.txt`
y ejecuta `manage.py runserver` desde la terminal integrada.

### Comandos útiles

```bash
python manage.py entrenar_modelos --evaluar   # reentrena y muestra MAE, RMSE y R²
python manage.py cargar_datos --reemplazar    # recarga las 16 500 visitas desde datos/
python manage.py cargar_datos --reemplazar --csv ruta/otro.csv   # usar otro CSV
```

Las visitas que se registran en la web aparecen al instante en el historial y el Dashboard.
El modelo las considera cuando ejecutas `entrenar_modelos`.

> Si faltan los archivos `.joblib`, o fueron creados con otra versión de scikit-learn,
> la web los **vuelve a entrenar sola** la primera vez que se consulta (tarda unos segundos).
> En ese caso, los números pueden variar muy poco respecto al PDF.

---

## 2. Subirlo a GitHub

Desde la carpeta del proyecto:

```bash
git init
git add .
git commit -m "FIEI Visitas - web Django"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/TU_REPO.git
git push -u origin main
```

`db.sqlite3` y los `.joblib` se suben a propósito (el más grande pesa unos 11 MB).
Si subes los archivos arrastrándolos en la página de GitHub, el límite es 25 MB por archivo: cabe.

---

## 3. Desplegarlo en PythonAnywhere (plan gratuito «Beginner»)

Reemplaza `TU_USUARIO` y `TU_REPO` por los tuyos.

**Paso 1. Clonar e instalar** (pestaña *Consoles* → *Bash*):

```bash
git clone https://github.com/TU_USUARIO/TU_REPO.git
cd TU_REPO
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py collectstatic --noinput
```

Si `pip install` falla por falta de espacio (*Disk quota exceeded*), recrea el entorno reutilizando
las librerías que ya trae PythonAnywhere:
`rm -rf venv && python3 -m venv --system-site-packages venv`, y vuelve a instalar.

**Paso 2. Crear la web** (pestaña *Web* → *Add a new web app*):
1. *Manual configuration* y la **misma versión de Python** con la que creaste el `venv`.
2. **Source code:** `/home/TU_USUARIO/TU_REPO`
3. **Virtualenv:** `/home/TU_USUARIO/TU_REPO/venv`
4. **Static files:** URL `/static/` → directorio `/home/TU_USUARIO/TU_REPO/staticfiles`

**Paso 3. Archivo WSGI** (enlace «WSGI configuration file» en la pestaña *Web*). Borra todo su contenido y pega:

```python
import os
import sys

ruta = '/home/TU_USUARIO/TU_REPO'
if ruta not in sys.path:
    sys.path.insert(0, ruta)

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

**Paso 4.** Pulsa **Reload** y abre `https://TU_USUARIO.pythonanywhere.com`.

### Si algo falla
- Pantalla de error o 500: abre el **Error log** de la pestaña *Web* y copia las últimas líneas.
- Se ve sin colores ni gráficos: revisa el mapeo de *Static files* y vuelve a correr `collectstatic`.
- `DisallowedHost`: tu dominio no está en `ALLOWED_HOSTS` de `config/settings.py`
  (ya acepta cualquier `*.pythonanywhere.com`).

### Límites del plan gratis (confírmalos en pythonanywhere.com/pricing)
- La web **vence al mes**: entra a la pestaña *Web* y pulsa el botón para extenderla antes de la exposición.
- 100 segundos de CPU al día y 512 MiB de disco: sobra para una demostración.
- Las visitas que se registren en el servidor quedan en `db.sqlite3` del servidor.
  Si luego haces `git pull`, ese archivo puede dar conflicto.

---

## Cómo se relaciona con el notebook y la presentación

| Notebook (Colab) | En la web |
|---|---|
| Secciones 3 y 4 (generar y validar 16 500 visitas) | `cargar_datos` y la tabla `Visita` |
| Sección 5 (resumen por piso, gráficos) | Dashboard |
| Sección 6 (historial con `PISO_HISTORIAL`) | Historial (filtro por piso) |
| Sección 15 (registrar una visita) | Registrar |
| Secciones 7 y 9 (tablas de conteos y entrenamiento) | `ml.py`, `entrenar_modelos` |
| Secciones 13 y 14 (`consultar` y siete días) | Afluencia |

Los datos son **sintéticos**: las estimaciones no representan el movimiento real de la FIEI.
