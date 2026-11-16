# CLAUDE.md · Air Lincoln No-show

Contexto para el asistente. Las reglas que **siempre** deben cumplirse están en el pipeline (`.github/workflows/validar-datos.yml`), no aquí.

## Qué es
Tablero de Streamlit para predecir no-show con `data/AIRLINCOLNDATA2.csv` (10,000 pasajeros). Tres usuarios: Laura (sobreventa), Armando (contacto con pasajeros) y Anna (calidad y modelo).

## Cómo verificar tu trabajo (obligatorio antes de decir "terminado")
- `python scripts/validar_datos.py` → salida sana: termina con `✓ El archivo cumple el contrato de datos`.
- `python -m pytest -q` → salida sana: `20 passed`.
- `streamlit run app.py` → arriba aparece «Revisión de tipos: ✓ cumple el contrato».

## Convenciones (con excepciones: usa criterio)
- No publiques agregados con menos de 30 pasajeros; la excepción es la vista restringida con seudónimos.
- Toda cifra nueva lleva su etiqueta: Dato, Calculado o Simulado.
- No uses edad ni género como criterio de intervención.
- Si agregas una columna al tablero, agrégala también a `contrato-datos.md` y a `core/contract.py`.
- No cambies las pruebas para que pasen; corrige el código.
