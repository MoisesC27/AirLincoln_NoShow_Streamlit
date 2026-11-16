"""Genera data/vuelos.csv: itinerario de referencia de Air Lincoln.

El archivo de pasajeros no trae número de vuelo, ruta ni fecha, así que este itinerario se arma con
aeropuertos reales y la configuración de asientos típica de cada avión. Se puede reemplazar por el
itinerario real con las mismas columnas (ver contrato-datos.md, sección D).
"""
import csv
from pathlib import Path

CIUDAD = {
    "MEX": "Ciudad de México", "GDL": "Guadalajara", "MTY": "Monterrey", "CUN": "Cancún", "TIJ": "Tijuana",
    "MID": "Mérida", "OAX": "Oaxaca", "SJD": "Los Cabos", "PVR": "Puerto Vallarta", "BJX": "León/Bajío",
    "QRO": "Querétaro", "HMO": "Hermosillo", "CJS": "Ciudad Juárez", "LAX": "Los Ángeles", "JFK": "Nueva York",
    "MAD": "Madrid", "BOG": "Bogotá", "ORD": "Chicago", "MIA": "Miami", "DFW": "Dallas", "IAH": "Houston",
    "PHX": "Phoenix",
}
MEXICO = {"MEX", "GDL", "MTY", "CUN", "TIJ", "MID", "OAX", "SJD", "PVR", "BJX", "QRO", "HMO", "CJS"}
HUBS = {"MEX", "GDL", "MTY"}
# Asientos en configuración típica de dos clases para cada modelo.
AVION = {"A321neo": 230, "A320neo": 186, "Boeing 737-8": 166, "Boeing 787-8": 243, "Boeing 787-9": 274,
         "Embraer E190": 99, "Embraer E175": 76, "Embraer E170": 76}
DIARIO = "1234567"
RUTAS = [  # origen, destino, avión, horas de salida, días (1 = lunes)
    ("MEX", "CUN", "A321neo", ["06:10", "10:40", "15:20", "19:55"], DIARIO),
    ("MEX", "GDL", "Boeing 737-8", ["07:00", "13:30", "20:15"], DIARIO),
    ("MEX", "MTY", "Boeing 737-8", ["06:30", "12:10", "18:40"], DIARIO),
    ("MEX", "MTY", "Boeing 737-8", ["21:50"], "12345"),
    ("MEX", "TIJ", "A321neo", ["08:20", "17:45"], DIARIO),
    ("MEX", "MID", "Embraer E190", ["09:15", "16:30"], DIARIO),
    ("MEX", "OAX", "Embraer E170", ["07:40", "14:05"], DIARIO),
    ("MEX", "SJD", "A320neo", ["11:00"], DIARIO),
    ("MEX", "SJD", "A320neo", ["18:20"], "4567"),
    ("MEX", "PVR", "A320neo", ["09:50"], DIARIO),
    ("MEX", "LAX", "Boeing 737-8", ["08:45", "16:10"], DIARIO),
    ("MEX", "ORD", "Boeing 737-8", ["07:25"], DIARIO),
    ("MEX", "MIA", "A321neo", ["12:40"], DIARIO),
    ("MEX", "JFK", "Boeing 787-8", ["23:30"], DIARIO),
    ("MEX", "MAD", "Boeing 787-9", ["21:40"], DIARIO),
    ("MEX", "BOG", "Boeing 737-8", ["13:15"], "1357"),
    ("GDL", "TIJ", "A320neo", ["06:45", "14:30", "20:40"], DIARIO),
    ("GDL", "CUN", "A320neo", ["09:30"], DIARIO),
    ("GDL", "CUN", "A320neo", ["16:55"], "567"),
    ("GDL", "LAX", "A320neo", ["07:50", "15:40"], DIARIO),
    ("GDL", "ORD", "Boeing 737-8", ["11:20"], DIARIO),
    ("GDL", "MTY", "Embraer E190", ["08:10", "19:05"], "12345"),
    ("MTY", "CUN", "A320neo", ["10:15"], DIARIO),
    ("MTY", "DFW", "Embraer E175", ["06:55", "17:20"], DIARIO),
    ("MTY", "IAH", "Embraer E175", ["12:35"], DIARIO),
    ("MTY", "TIJ", "A320neo", ["15:10"], DIARIO),
    ("CUN", "MEX", "A321neo", ["07:30", "13:00", "21:15"], DIARIO),
    ("CUN", "MIA", "Boeing 737-8", ["11:45"], DIARIO),
    ("CUN", "DFW", "Boeing 737-8", ["14:20"], DIARIO),
    ("CUN", "LAX", "A320neo", ["19:40"], DIARIO),
    ("PVR", "DFW", "Embraer E175", ["18:25"], "567"),
    ("TIJ", "MEX", "A321neo", ["06:00", "23:10"], DIARIO),
    ("MID", "MEX", "Embraer E190", ["06:20", "18:50"], DIARIO),
    ("OAX", "MEX", "Embraer E170", ["10:20", "17:00"], DIARIO),
    ("SJD", "LAX", "A320neo", ["13:40"], "4567"),
    ("PVR", "LAX", "A320neo", ["12:50"], DIARIO),
    ("BJX", "MEX", "Embraer E170", ["07:15", "19:30"], "12345"),
    ("QRO", "IAH", "Embraer E175", ["08:35"], "12345"),
    ("HMO", "PHX", "Embraer E175", ["09:05"], "1357"),
    ("CJS", "GDL", "Embraer E190", ["06:35"], DIARIO),
]

COLS = ["vuelo", "origen", "ciudad_origen", "destino", "ciudad_destino", "salida", "dias", "avion", "asientos",
        "sale_de_hub", "internacional"]


def main(out: Path) -> None:
    filas = []
    for o, d, av, horas, dias in RUTAS:
        for h in horas:
            filas.append({"origen": o, "ciudad_origen": CIUDAD[o], "destino": d, "ciudad_destino": CIUDAD[d], "salida": h,
                          "dias": dias, "avion": av, "asientos": AVION[av], "sale_de_hub": int(o in HUBS),
                          "internacional": int(not (o in MEXICO and d in MEXICO))})
    filas.sort(key=lambda f: (f["salida"], f["origen"]))
    for i, f in enumerate(filas):
        f["vuelo"] = f"AL {100 + 2 * i}"
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        w.writerows(filas)
    print(f"{len(filas)} vuelos → {out}")


if __name__ == "__main__":
    main(Path(__file__).resolve().parents[1] / "data" / "vuelos.csv")
