from django.db import models

from .constants import DESTINOS, MOTIVOS, PISOS, TIPOS


class Visita(models.Model):
    """Una visita (una persona) que ingresa a la FIEI."""

    ingreso = models.DateTimeField("Ingreso", db_index=True)
    salida = models.DateTimeField("Salida", null=True, blank=True)
    piso = models.PositiveSmallIntegerField(
        "Piso", choices=[(p, f"Piso {p}") for p in PISOS], db_index=True
    )
    destino = models.CharField(
        "Destino",
        max_length=60,
        choices=[(d, d) for lista in DESTINOS.values() for d in lista],
    )
    tipo_visitante = models.CharField(
        "Tipo de visitante", max_length=20, choices=[(t, t.capitalize()) for t in TIPOS]
    )
    motivo = models.CharField(
        "Motivo", max_length=40, choices=[(m, m) for m in MOTIVOS]
    )

    class Meta:
        ordering = ["ingreso", "id"]
        verbose_name = "visita"
        verbose_name_plural = "visitas"

    def __str__(self):
        return f"Visita {self.pk} · piso {self.piso} · {self.ingreso:%d/%m/%Y %H:%M}"
