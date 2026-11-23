import time

from django.core.management.base import BaseCommand, CommandError

from visitas import ml


class Command(BaseCommand):
    help = (
        "Entrena los modelos Random Forest (HORA y DIA) con todas las visitas de la "
        "base de datos y los guarda en la carpeta modelos/."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--evaluar",
            action="store_true",
            help="Además calcula MAE, RMSE y R² con el último 20 %% de los días.",
        )

    def handle(self, *args, **opciones):
        inicio = time.time()
        try:
            metricas = ml.entrenar_modelos(con_evaluacion=opciones["evaluar"])
        except ValueError as error:
            raise CommandError(str(error))
        self.stdout.write(
            self.style.SUCCESS(f"Modelos entrenados y guardados en {time.time() - inicio:.1f} s.")
        )
        for modalidad, m in metricas.items():
            self.stdout.write(
                f"  {modalidad}: MAE={m['MAE']}  RMSE={m['RMSE']}  R²={m['R2']}  "
                f"(prueba desde {m['fecha_corte']})"
            )
