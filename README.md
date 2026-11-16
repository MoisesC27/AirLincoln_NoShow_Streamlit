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

Sin configuración la app funciona como vista pública (solo agregados). Para activar OIDC, roles y seudónimos,
copia `.streamlit/secrets.toml.example` como `.streamlit/secrets.toml` y complétalo. En Streamlit Community Cloud,
pega el contenido en *Settings → Secrets*.

## Pipeline de validación de datos (Entregable 2)

En cada push y pull request, GitHub Actions (`.github/workflows/validar-datos.yml`):
1. valida `data/AIRLINCOLNDATA2.csv` contra el contrato (`python scripts/validar_datos.py`);
2. corre las pruebas (`python -m pytest -q`).

Si el dato se rompe (texto en una columna numérica, código fuera de rango, columna faltante, variable derivada incoherente), la corrida queda en rojo y el cambio se detiene. El contrato está en [`contrato-datos.md`](contrato-datos.md).

### Prueba de que detiene un cambio malo

**Corrida que falló:** `PEGAR AQUÍ LA LIGA A LA CORRIDA EN ROJO`

Cómo se rompió a propósito:
1. Rama `prueba-dato-roto`: en la fila 6 del CSV, `No_Show` se cambió de `0` a `abc`.
2. Push → la acción falló con «No_Show: 1 valores con texto en una columna numérica».
3. Se borró la rama; `main` sigue en verde.
