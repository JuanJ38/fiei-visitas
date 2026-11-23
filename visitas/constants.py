"""Valores fijos del sistema (los mismos que usa el notebook de Colab)."""

PISOS = [1, 2, 3, 4, 5]

# Destinos posibles de cada piso
DESTINOS = {
    1: ["Secretaría", "Mesa de partes"],
    2: ["Aulas académicas", "Coordinación académica"],
    3: ["Laboratorios", "Soporte técnico"],
    4: ["Oficinas docentes", "Sala de reuniones"],
    5: ["Biblioteca", "Sala de estudio"],
}

MOTIVOS = [
    "Trámite",
    "Consulta",
    "Reunión",
    "Entrega de documentos",
    "Visita programada",
]

TIPOS = ["EXTERNO", "EGRESADO", "PROVEEDOR", "INVITADO"]

# Piso 0 = toda la FIEI (suma de los cinco pisos), solo para predicciones.
PISOS_CONSULTA = [0] + PISOS

DIAS_SEMANA = [
    "lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo",
]
