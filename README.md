# Air Lincoln · Inteligencia de No-show (Streamlit)

## Ejecutar en Visual Studio Code (Windows)

En la terminal, dentro de esta carpeta:

```powershell
python -m venv .venv                                   # solo la primera vez (omitir si .venv ya existe)
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m streamlit run app.py
```

La primera carga entrena los 5 modelos (≈20 s); después queda en caché.

Pruebas de cálculo: `.venv\Scripts\python.exe -m pip install pytest` y luego `.venv\Scripts\python.exe -m pytest -q`

## Estructura

| Carpeta | Contenido |
|---|---|
| `app.py` | Entrada: encabezado global, selector de perfil y manejo de errores |
| `core/` | Datos, modelos, simulador de sobreventa, calidad, reglas de intervención, seguridad y textos |
| `ui/` | Tema oscuro, componentes, gráficas Plotly y estado de sesión |
| `views/` | Laura, Armando, Anna y Acerca del producto |
| `data/` | `AIRLINCOLNDATA2.csv` (y opcionalmente `particion.csv` con la partición oficial) |
| `tests/` | Pruebas de consistencia numérica |

## Inicio de sesión (opcional)

## Dashboard público

Primera iteración del dashboard de Air Lincoln:

https://TU-URL-DE-STREAMLIT.streamlit.app

### Decisión que habilita

El dashboard ayuda a estimar cuántos boletos adicionales conviene vender para un vuelo considerando el riesgo de No-show, el costo de asientos vacíos y el riesgo de negar abordaje.
