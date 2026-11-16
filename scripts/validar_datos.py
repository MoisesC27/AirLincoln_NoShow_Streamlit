"""Valida data/AIRLINCOLNDATA2.csv contra el contrato de datos. Sale con código 1 si no cumple.

Uso:  python scripts/validar_datos.py [ruta_al_csv]
Lo ejecuta GitHub Actions en cada push y pull request (.github/workflows/validar-datos.yml).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.contract import read_and_check  # noqa: E402


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "AIRLINCOLNDATA2.csv"
    res = read_and_check(path)
    print(f"Archivo: {path.name}")
    print(res.report.to_string(index=False))
    print(f"\nFilas válidas: {len(res.df):,} · excluidas por 'sin dato': {res.excluded_rows} · "
          f"caracteres invisibles corregidos: {res.invisible_rows} · recalculadas: {res.recalculated or 0}")
    if res.missing_tokens_found:
        print("Marcas de 'no hay dato' encontradas:", res.missing_tokens_found)
    if not res.ok:
        print("\n✕ EL ARCHIVO NO CUMPLE EL CONTRATO DE DATOS:")
        for p in res.problems:
            print("  -", p)
        return 1
    print("\n✓ El archivo cumple el contrato de datos: ninguna columna numérica quedó como texto.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
