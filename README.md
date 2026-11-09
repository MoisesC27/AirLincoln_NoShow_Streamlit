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

https://airlincolnnoshowapp-wmhdr236rczouegkvt8wcv.streamlit.app/

### Decisión que habilita

El dashboard ayuda a estimar cuántos boletos adicionales conviene vender para un vuelo considerando el riesgo de No-show, el costo de asientos vacíos y el riesgo de negar abordaje.
### Objetivo de negocio

Air Lincoln enfrenta el problema de pasajeros que reservan un vuelo pero finalmente no se presentan. Cuando esto ocurre, algunos asientos pueden quedar vacíos y representar una pérdida de ingreso o capacidad desaprovechada.

**Línea base:** operar sin una recomendación analítica de sobreventa, aceptando el riesgo de que algunos asientos queden vacíos por No-show.

**Meta:** reducir el costo esperado asociado con los asientos vacíos, buscando al mismo tiempo mantener controlado el riesgo de negar abordaje a un pasajero.

**Decisión que habilita:** determinar cuántos boletos adicionales conviene vender para un vuelo específico de acuerdo con sus condiciones, la probabilidad estimada de No-show y los costos definidos por el usuario.