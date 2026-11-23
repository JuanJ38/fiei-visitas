from pathlib import Path

import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from visitas.constants import DESTINOS, MOTIVOS, PISOS, TIPOS
from visitas.models import Visita


class Command(BaseCommand):
    help = (
        "Carga las visitas del CSV que genera el notebook "
        "(visitas_fiei_16500_sinteticas.csv) en la base de datos."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--csv", help="Ruta de otro CSV (por defecto: datos/visitas_fiei_16500_sinteticas.csv)"
        )
        parser.add_argument(
            "--reemplazar",
            action="store_true",
            help="Borra las visitas actuales antes de cargar.",
        )

    def handle(self, *args, **opciones):
        ruta = Path(opciones["csv"]) if opciones["csv"] else settings.DATOS_CSV
        if not ruta.exists():
            raise CommandError(f"No se encontró el archivo: {ruta}")

        existentes = Visita.objects.count()
        if existentes and not opciones["reemplazar"]:
            self.stdout.write(
                self.style.WARNING(
                    f"Ya hay {existentes} visitas en la base. "
                    "Usa --reemplazar para cargarlas de nuevo."
                )
            )
            return

        df = pd.read_csv(ruta)
        if not {"ingreso", "piso"} <= set(df.columns):
            raise CommandError("El CSV debe tener al menos las columnas 'ingreso' y 'piso'.")

        # Misma validación que la sección 4 del notebook
        df["ingreso"] = pd.to_datetime(df["ingreso"], errors="coerce")
        df["piso"] = pd.to_numeric(df["piso"], errors="coerce")
        df = df.dropna(subset=["ingreso", "piso"])
        df = df[df["piso"].isin(PISOS)].copy()
        df["piso"] = df["piso"].astype(int)
        df = df.sort_values("ingreso", kind="stable").reset_index(drop=True)

        if "salida" in df.columns:
            df["salida"] = pd.to_datetime(df["salida"], errors="coerce")
        else:
            df["salida"] = pd.NaT
        for col, valor in (("destino", None), ("tipo_visitante", TIPOS[0]), ("motivo", MOTIVOS[0])):
            if col not in df.columns:
                df[col] = valor

        visitas = []
        for fila in df.itertuples(index=False):
            visitas.append(
                Visita(
                    ingreso=fila.ingreso.to_pydatetime(),
                    salida=fila.salida.to_pydatetime() if pd.notna(fila.salida) else None,
                    piso=fila.piso,
                    destino=fila.destino if isinstance(fila.destino, str) else DESTINOS[fila.piso][0],
                    tipo_visitante=fila.tipo_visitante,
                    motivo=fila.motivo,
                )
            )

        if opciones["reemplazar"]:
            Visita.objects.all().delete()
        Visita.objects.bulk_create(visitas, batch_size=2000)
        self.stdout.write(self.style.SUCCESS(f"Se cargaron {len(visitas)} visitas."))
        self.stdout.write("Si cambiaste los datos, ejecuta: python manage.py entrenar_modelos")
