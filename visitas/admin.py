from django.contrib import admin

from .models import Visita


@admin.register(Visita)
class VisitaAdmin(admin.ModelAdmin):
    list_display = ("id", "ingreso", "piso", "destino", "tipo_visitante", "motivo")
    list_filter = ("piso", "tipo_visitante", "motivo")
    date_hierarchy = "ingreso"
