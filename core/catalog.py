"""Catálogo: nombres de variables, etiquetas y constantes del proyecto.

Las etiquetas provienen del diccionario de variables del Equipo 4
(Diccionario_Variables_Passenger_No_Show.docx).
"""

TARGET = "No_Show"
ID_COL = "Customer_ID"

# 11 predictores definidos en la Entrega 3 (Tabla 3).
FEATURES = [
    "Age",
    "Booking_Class",
    "Business_Traveler",
    "Connections",
    "Departure_Day",
    "Departure_Hour",
    "Frequent_Flier_Status",
    "International_Flight",
    "When_Ticket_Purchased",
    "Weather_Issues",
    "Weather_Issues___Connection",
]

EXPECTED_COLUMNS = [
    "Customer_ID", "No_Show", "Major_Hub_Departure", "Departure_Day", "Departure_Hour",
    "Connections", "International_Flight", "Connection___International_Fligh",
    "Business_Traveler", "Booking_Class", "When_Ticket_Purchased", "Age",
    "Gender___Female", "Frequent_Flier_Status", "Weather_Issues", "Weather_Issues___Connection",
]

# Valores válidos por columna (diccionario de datos).
VALID_VALUES = {
    "No_Show": {0, 1},
    "Major_Hub_Departure": {0, 1},
    "Departure_Day": set(range(1, 8)),
    "Departure_Hour": {1, 2, 3},
    "Connections": {0, 1},
    "International_Flight": {0, 1},
    "Connection___International_Fligh": {0, 1},
    "Business_Traveler": {0, 1},
    "Booking_Class": {1, 2, 3},
    "When_Ticket_Purchased": {1, 2, 3},
    "Age": set(range(1, 9)),
    "Gender___Female": {0, 1},
    "Frequent_Flier_Status": {0, 1},
    "Weather_Issues": {0, 1},
    "Weather_Issues___Connection": {0, 1},
}

DAYS = {1: "Lunes", 2: "Martes", 3: "Miércoles", 4: "Jueves", 5: "Viernes", 6: "Sábado", 7: "Domingo"}
DAYS_SHORT = {1: "Lun", 2: "Mar", 3: "Mié", 4: "Jue", 5: "Vie", 6: "Sáb", 7: "Dom"}
HOURS = {1: "Mañana (6–12 h)", 2: "Tarde (12–18 h)", 3: "Noche (18–6 h)"}
HOURS_SHORT = {1: "Mañana", 2: "Tarde", 3: "Noche"}
AGES = {1: "0–10", 2: "11–20", 3: "21–30", 4: "31–40", 5: "41–50", 6: "51–60", 7: "61–70", 8: "71+"}
CLASSES = {1: "Primera", 2: "Business", 3: "Coach"}
PURCHASE = {1: "2+ semanas antes", 2: "Menos de 2 semanas", 3: "El mismo día"}
YESNO = {1: "Sí", 0: "No"}

VALUE_LABELS = {
    "Age": {k: f"Edad {v}" for k, v in AGES.items()},
    "Booking_Class": {1: "Primera clase", 2: "Clase Business", 3: "Clase Coach"},
    "Business_Traveler": {0: "No viaja por negocios", 1: "Viaja por negocios"},
    "Connections": {0: "Sin conexión", 1: "Con conexión"},
    "Departure_Day": {k: f"Sale en {v.lower()}" for k, v in DAYS.items()},
    "Departure_Hour": {1: "Sale en la mañana", 2: "Sale en la tarde", 3: "Sale de noche"},
    "Frequent_Flier_Status": {0: "No es viajero frecuente", 1: "Viajero frecuente"},
    "International_Flight": {0: "Vuelo nacional", 1: "Vuelo internacional"},
    "When_Ticket_Purchased": {1: "Compra 2+ semanas antes", 2: "Compra < 2 semanas antes", 3: "Compra el mismo día"},
    "Weather_Issues": {0: "Sin mal clima", 1: "Mal clima"},
    "Weather_Issues___Connection": {0: "Sin (mal clima + conexión)", 1: "Mal clima + conexión"},
}

FEATURE_NAMES = {
    "Age": "Edad",
    "Booking_Class": "Clase",
    "Business_Traveler": "Viaje de negocios",
    "Connections": "Conexión",
    "Departure_Day": "Día de salida",
    "Departure_Hour": "Horario de salida",
    "Frequent_Flier_Status": "Viajero frecuente",
    "International_Flight": "Vuelo internacional",
    "When_Ticket_Purchased": "Anticipación de compra",
    "Weather_Issues": "Mal clima",
    "Weather_Issues___Connection": "Mal clima + conexión",
    "Major_Hub_Departure": "Salida desde hub",
}

PARTITION_LABELS = {"train": "Entrenamiento", "valid": "Validación", "test": "Prueba"}

# Política del proyecto: no se publican agregados con menos de 30 registros.
MIN_N = 30
RANDOM_STATE = 42
