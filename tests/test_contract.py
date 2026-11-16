"""Pruebas del contrato de datos: comprueban que la validación detiene un archivo roto."""
import pandas as pd

from core.contract import check, read_and_check
from core.data import DATA_FILE


def _raw():
    return pd.read_csv(DATA_FILE, dtype=str, encoding="utf-8-sig", keep_default_na=False)


def test_archivo_real_cumple():
    res = read_and_check(DATA_FILE)
    assert res.ok, res.problems
    assert len(res.df) == 10_000 and res.invisible_rows == 4
    assert all(pd.api.types.is_numeric_dtype(res.df[c]) for c in res.df.columns)


def test_texto_en_columna_numerica_se_detiene():
    raw = _raw()
    raw.loc[5, "Booking_Class"] = "Primera"
    res = check(raw)
    assert not res.ok
    assert any("Booking_Class" in p and "texto" in p for p in res.problems)


def test_codigo_fuera_de_rango_se_detiene():
    raw = _raw()
    raw.loc[0, "Departure_Day"] = "9"
    assert not check(raw).ok


def test_columna_faltante_se_detiene():
    assert not check(_raw().drop(columns=["No_Show"])).ok


def test_marcas_de_vacio_sin_dato_excluyen_fila():
    raw = _raw()
    raw.loc[[1, 2], "Weather_Issues"] = ["NA", ""]
    res = check(raw)
    assert res.ok and res.excluded_rows == 2 and len(res.df) == 9_998


def test_derivada_vacia_se_recalcula():
    raw = _raw()
    raw.loc[3, "Weather_Issues___Connection"] = ""
    res = check(raw)
    assert res.ok and res.recalculated == {"Weather_Issues___Connection": 1}


def test_no_aplica_se_conserva():
    raw = _raw()
    raw.loc[4, "Gender___Female"] = "null"
    res = check(raw)
    assert res.ok and res.excluded_rows == 0 and res.df["Gender___Female"].isna().sum() == 1


def test_filas_con_error_se_excluyen_y_el_archivo_sigue_usable():
    raw = _raw()
    raw.loc[5, "Booking_Class"] = "Primera"
    raw.loc[6, "Departure_Day"] = "9"
    res = check(raw)
    assert not res.ok and res.usable           # el pipeline lo detiene, la app lo muestra con aviso
    assert res.invalid_rows == 2 and res.error_rows == [7, 8] and len(res.df) == 9_998


def test_columnas_opcionales_vuelo_y_fecha():
    import pandas as pd
    from core.contract import check
    raw = pd.read_csv("data/AIRLINCOLNDATA2.csv", dtype=str, keep_default_na=False, encoding="utf-8-sig").head(400)
    vuelos = pd.read_csv("data/vuelos.csv", dtype=str)
    raw["Flight_Date"] = ""
    raw["Flight_Number"] = ""
    ok = check(raw, vuelos)
    assert ok.ok and len(ok.df) == 400          # vacías: no aplica, la fila se conserva
    raw.loc[0, "Flight_Date"] = "31/02/2026"
    raw.loc[1, "Flight_Number"] = "AL 999"
    res = check(raw, vuelos)
    assert not res.ok and res.usable and res.invalid_rows == 2 and len(res.df) == 398


def test_fecha_debe_caer_en_departure_day():
    import pandas as pd
    from core.contract import check
    raw = pd.read_csv("data/AIRLINCOLNDATA2.csv", dtype=str, keep_default_na=False, encoding="utf-8-sig").head(50)
    lunes = pd.Timestamp("2026-06-01")  # lunes
    raw["Flight_Date"] = [(lunes + pd.Timedelta(days=int(str(d).replace("﻿", "").strip('"')) - 1)).strftime("%Y-%m-%d") for d in raw["Departure_Day"]]
    assert check(raw).ok
    raw.loc[0, "Flight_Date"] = (pd.Timestamp(raw.loc[0, "Flight_Date"]) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    res = check(raw)
    assert not res.ok and res.invalid_rows == 1
