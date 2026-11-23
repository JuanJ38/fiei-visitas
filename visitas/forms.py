from datetime import datetime

from django import forms

from .constants import DESTINOS, MOTIVOS, PISOS, PISOS_CONSULTA, TIPOS


def _todos_los_destinos():
    return [(d, d) for piso in PISOS for d in DESTINOS[piso]]


class RegistroForm(forms.Form):
    """Formulario para registrar visitas (pantalla «Registrar visitas»)."""

    piso = forms.TypedChoiceField(
        label="Piso",
        choices=[(p, f"Piso {p}") for p in PISOS],
        coerce=int,
    )
    destino = forms.ChoiceField(label="Destino", choices=_todos_los_destinos())
    ingreso = forms.DateTimeField(
        label="Fecha y hora de ingreso",
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
        ),
        input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M"],
    )
    tipo_visitante = forms.ChoiceField(
        label="Tipo de visitante", choices=[(t, t.capitalize()) for t in TIPOS]
    )
    motivo = forms.ChoiceField(label="Motivo", choices=[(m, m) for m in MOTIVOS])
    cantidad = forms.IntegerField(
        label="Cantidad de personas", min_value=1, max_value=50, initial=1
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.fields["ingreso"].initial = datetime.now().replace(
                second=0, microsecond=0
            )

    def clean(self):
        datos = super().clean()
        piso, destino = datos.get("piso"), datos.get("destino")
        if piso and destino and destino not in DESTINOS[piso]:
            self.add_error("destino", f"Ese destino no pertenece al piso {piso}.")
        return datos


class AfluenciaForm(forms.Form):
    """Parámetros de la consulta de afluencia esperada."""

    fecha = forms.DateField(
        label="Fecha",
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        input_formats=["%Y-%m-%d", "%d/%m/%Y"],
    )
    piso = forms.TypedChoiceField(
        label="Piso",
        choices=[(p, "Toda la FIEI" if p == 0 else f"Piso {p}") for p in PISOS_CONSULTA],
        coerce=int,
    )
    modalidad = forms.ChoiceField(
        label="Modalidad",
        choices=[("DIA", "Por día (próximos 7 días)"), ("HORA", "Por hora (24 franjas)")],
    )
