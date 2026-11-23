from datetime import date, timedelta

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.shortcuts import redirect, render

from visitas import ml
from .constants import DESTINOS, DIAS_SEMANA, PISOS
from .forms import AfluenciaForm, RegistroForm
from .models import Visita

# Fecha de ejemplo de la pantalla de afluencia (la misma del PDF y del notebook).
FECHA_EJEMPLO = date(2026, 11, 18)


# --------------------------------------------------------------------------
# 1. Dashboard
# --------------------------------------------------------------------------
def dashboard(request):
    total = Visita.objects.count()
    conteo = {
        fila["piso"]: fila["n"]
        for fila in Visita.objects.values("piso").annotate(n=Count("id"))
    }
    pisos = [
        {
            "piso": p,
            "visitas": conteo.get(p, 0),
            "porcentaje": round(100 * conteo.get(p, 0) / total, 2) if total else 0,
        }
        for p in PISOS
    ]

    # Evolución diaria (los días sin visitas cuentan como 0, igual que el notebook)
    por_dia = {
        fila["dia"]: fila["n"]
        for fila in Visita.objects.annotate(dia=TruncDate("ingreso"))
        .values("dia")
        .annotate(n=Count("id"))
    }
    etiquetas, valores = [], []
    if por_dia:
        dia, ultimo = min(por_dia), max(por_dia)
        while dia <= ultimo:
            etiquetas.append(dia.strftime("%d/%m/%Y"))
            valores.append(por_dia.get(dia, 0))
            dia += timedelta(days=1)

    contexto = {
        "total": total,
        "pisos": pisos,
        "dias_con_datos": len(etiquetas),
        "rango": (etiquetas[0], etiquetas[-1]) if etiquetas else None,
        "grafico_pisos": {
            "etiquetas": [f"Piso {p['piso']}" for p in pisos],
            "valores": [p["visitas"] for p in pisos],
        },
        "grafico_diario": {"etiquetas": etiquetas, "valores": valores},
    }
    return render(request, "visitas/dashboard.html", contexto)


# --------------------------------------------------------------------------
# 2. Registrar visitas
# --------------------------------------------------------------------------
def registrar(request):
    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            # Una visita por persona (así cuenta el modelo: cada fila es una visita).
            Visita.objects.bulk_create(
                [
                    Visita(
                        ingreso=d["ingreso"],
                        salida=d["ingreso"] + timedelta(minutes=60),
                        piso=d["piso"],
                        destino=d["destino"],
                        tipo_visitante=d["tipo_visitante"],
                        motivo=d["motivo"],
                    )
                    for _ in range(d["cantidad"])
                ]
            )
            messages.success(
                request,
                f"Se registró {d['cantidad']} visita(s) en el piso {d['piso']} "
                f"({d['destino']}).",
            )
            return redirect("registrar")
    else:
        form = RegistroForm()
    return render(
        request,
        "visitas/registrar.html",
        {"form": form, "destinos": {str(p): DESTINOS[p] for p in PISOS}},
    )


# --------------------------------------------------------------------------
# 3. Historial de visitas
# --------------------------------------------------------------------------
def historial(request):
    piso = request.GET.get("piso", "")
    consulta = Visita.objects.order_by("-ingreso", "-id")
    if piso.isdigit() and int(piso) in PISOS:
        consulta = consulta.filter(piso=int(piso))
    else:
        piso = ""

    pagina = Paginator(consulta, 25).get_page(request.GET.get("pagina"))
    return render(
        request,
        "visitas/historial.html",
        {"pagina": pagina, "piso": piso, "pisos": PISOS},
    )


# --------------------------------------------------------------------------
# 4. Consulta de afluencia
# --------------------------------------------------------------------------
# --------------------------------------------------------------------------
# 5. Modelo: evaluación, línea base e importancia de variables
# --------------------------------------------------------------------------
def modelo(request):
    evaluacion = ml.obtener_evaluacion()
    nombres = {"HORA": "Por hora", "DIA": "Por día"}
    filas = []
    for clave in ("HORA", "DIA"):
        m = evaluacion["modelos"][clave]
        filas.append({**m, "nombre": nombres[clave]})
    dia = evaluacion["modelos"]["DIA"]

    contexto = {
        "evaluacion": evaluacion,
        "filas": filas,
        "base_mejor": all(f["MAE_base"] < f["MAE"] for f in filas),
        "corte": {
            "entrenamiento_hasta": date.fromisoformat(dia["entrenamiento_hasta"]),
            "desde": date.fromisoformat(dia["fecha_corte"]),
            "dias_entrenamiento": dia["dias_entrenamiento"],
            "dias_prueba": dia["dias_prueba"],
            "total_dias": dia["dias_entrenamiento"] + dia["dias_prueba"],
        },
        "importancias": ml.importancias(),
        "serie": dia["serie"],
    }
    return render(request, "visitas/modelo.html", contexto)


def _etiqueta_dia(f):
    return f"{DIAS_SEMANA[f.weekday()][:3]} {f:%d/%m}"


def afluencia(request):
    inicial = {"fecha": FECHA_EJEMPLO, "piso": 0, "modalidad": "DIA"}
    if request.GET:
        form = AfluenciaForm(request.GET)
        valores = form.cleaned_data if form.is_valid() else None
    else:
        form = AfluenciaForm(initial=inicial)
        valores = inicial  # al abrir la pantalla se muestra el ejemplo del PDF

    contexto = {"form": form}
    if valores:
        fecha, piso, modalidad = valores["fecha"], valores["piso"], valores["modalidad"]
        alcance = "toda la FIEI (suma de los cinco pisos)" if piso == 0 else f"el piso {piso}"
        contexto.update(modalidad=modalidad, alcance=alcance, fecha=fecha, piso=piso)

        if modalidad == "DIA":
            filas = ml.pronostico_dias(fecha, piso, dias=7)
            for fila in filas:
                fila["nombre_dia"] = DIAS_SEMANA[fila["fecha"].weekday()]
                fila["fin_de_semana"] = fila["fecha"].weekday() >= 5
            contexto.update(
                filas=filas,
                principal=filas[0],
                mayor=max(filas, key=lambda f: f["visitas"]),
                menor=min(filas, key=lambda f: f["visitas"]),
                grafico={
                    "etiquetas": [_etiqueta_dia(f["fecha"]) for f in filas],
                    "valores": [f["visitas"] for f in filas],
                    "fines": [f["fin_de_semana"] for f in filas],
                    "titulo": "Visitas estimadas por día",
                },
            )
        else:
            filas = ml.consultar(fecha, piso, "HORA")
            for fila in filas:
                fila["rango"] = f"{fila['hora']:02d}:00 - {fila['hora']:02d}:59"
            pico = max(filas, key=lambda f: f["visitas"])
            contexto.update(
                filas=filas,
                total=round(sum(f["visitas"] for f in filas), 1),
                pico=pico,
                dia_nombre=DIAS_SEMANA[fecha.weekday()],
                grafico={
                    "etiquetas": [f"{f['hora']:02d}h" for f in filas],
                    "valores": [f["visitas"] for f in filas],
                    "fines": [False] * len(filas),
                    "titulo": "Visitas estimadas por hora",
                },
            )
    return render(request, "visitas/afluencia.html", contexto)
