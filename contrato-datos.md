# Contrato de datos · Air Lincoln No-show

Versión 1 · Entregable 2 (Build y Test). La versión que se ejecuta está en `core/contract.py`; si se cambia algo aquí, se cambia también allá.
La revisión corre **antes de dibujar el tablero** (`app.py`) y en **cada cambio del repositorio** (`.github/workflows/validar-datos.yml`).

## Decisiones sobre celdas vacías

> Propuesta del equipo. Pendiente de confirmar en clase.

| Significado | Qué hace el tablero | Columnas |
|---|---|---|
| **Sin dato**: el valor existe pero no se registró | La fila se excluye del análisis y el número de filas excluidas se muestra en la app | Todas las que usa el modelo y `No_Show` |
| **No aplica**: la columna no se usa en el tablero ni en el modelo | Se conserva vacía; no excluye la fila | `Gender___Female` |
| **Se recalcula / cero**: columna derivada de otras dos | Se recalcula con sus componentes; vale **0** cuando no se cumplen ambas condiciones | `Connection___International_Fligh`, `Weather_Issues___Connection` |
| **Dato inválido**: texto en una columna numérica, decimal, código fuera de rango o combinada incoherente | La app **no se detiene**: excluye esas filas, muestra el aviso rojo con su número de fila y dibuja el tablero con las filas válidas. El **pipeline sí detiene** el cambio | Todas |

**Marcas de "no hay dato" que se convierten a vacío antes de revisar tipos:** celda vacía, `NA`, `N/A`, `nan`, `null`, `none`, `-`, `--`, `?`, `#N/A`, `sin dato`, `s/d` (sin importar mayúsculas).

**Caracteres invisibles que se eliminan:** BOM (`﻿`), espacio de ancho cero y espacio duro. En el archivo actual hay **4 BOM** incrustados (filas 2001, 4001, 6001 y 8001), porque el CSV se unió desde 5 partes. Sin limpiarlos, esos 4 `Customer_ID` se leían como texto y la conversión a número fallaba.

**Hallazgo del archivo actual:** no tiene celdas vacías ni marcas de "no hay dato"; las 10,000 filas pasan. Las reglas de arriba se probaron con archivos modificados en `tests/test_contract.py`.

## A. Archivo de entrada: `data/AIRLINCOLNDATA2.csv`

| Columna | Tipo | Unidad / códigos | De dónde viene | Vacío significa |
|---|---|---|---|---|
| `Customer_ID` | entero | identificador del pasajero | Archivo | Sin dato → se excluye la fila |
| `No_Show` | entero | 0 = se presentó, 1 = no se presentó | Archivo | Sin dato → se excluye la fila |
| `Major_Hub_Departure` | entero | 0/1 (1 = sale de un hub) | Archivo | Sin dato → se excluye la fila |
| `Departure_Day` | entero | 1 = lunes … 7 = domingo | Archivo | Sin dato → se excluye la fila |
| `Departure_Hour` | entero | 1 = mañana (6–12), 2 = tarde (12–18), 3 = noche (18–6) | Archivo | Sin dato → se excluye la fila |
| `Connections` | entero | 0/1 (1 = tiene conexión) | Archivo | Sin dato → se excluye la fila |
| `International_Flight` | entero | 0/1 (1 = internacional) | Archivo | Sin dato → se excluye la fila |
| `Connection___International_Fligh` | entero | 0/1, derivada: conexión **y** internacional | Archivo (se verifica contra sus componentes) | Se recalcula; 0 si no se cumplen ambas |
| `Business_Traveler` | entero | 0/1 | Archivo | Sin dato → se excluye la fila |
| `Booking_Class` | entero | 1 = Primera, 2 = Business, 3 = Coach | Archivo | Sin dato → se excluye la fila |
| `When_Ticket_Purchased` | entero | 1 = 2+ semanas, 2 = menos de 2 semanas, 3 = mismo día | Archivo | Sin dato → se excluye la fila |
| `Age` | entero | rango de edad 1–8 (0–10 … 71+) | Archivo | Sin dato → se excluye la fila |
| `Gender___Female` | entero | 0/1 | Archivo | No aplica → se deja vacío (no se usa) |
| `Frequent_Flier_Status` | entero | 0/1 | Archivo | Sin dato → se excluye la fila |
| `Weather_Issues` | entero | 0/1 (1 = mal clima) | Archivo | Sin dato → se excluye la fila |
| `Weather_Issues___Connection` | entero | 0/1, derivada: mal clima **y** conexión | Archivo (se verifica contra sus componentes) | Se recalcula; 0 si no se cumplen ambas |
| `Flight_Number` *(opcional)* | texto | número de vuelo `AL 123`; debe existir en el itinerario y coincidir con día, horario, hub y destino del pasajero | Archivo | No aplica → se deja vacío; la fila se conserva |
| `Flight_Date` *(opcional)* | fecha | `AAAA-MM-DD`; su día de la semana debe ser `Departure_Day` | Archivo | No aplica → se deja vacío; la fila se conserva |

**En la app**, un archivo con datos inválidos se muestra con aviso rojo y sin esas filas; solo se rechaza si le faltan columnas o no le quedan filas válidas. **El pipeline detiene el cambio cuando:** falta una columna, aparece una columna no declarada, hay texto en una columna numérica, hay decimales, un código está fuera de su lista o una variable derivada no coincide con sus componentes.

## B. Tabla publicada en el tablero (sección de Laura): «Tipos de vuelo: costo de no-show y sobreventa»

Un renglón por combinación de día × horario × hub × destino con 30 pasajeros o más (política de supresión n < 30). El encabezado de cada columna dice su origen entre corchetes.

| Columna | Tipo | Unidad | De dónde viene | Vacío significa |
|---|---|---|---|---|
| Día | texto | lunes … domingo | **Dato**: `Departure_Day` | No puede estar vacío (es la llave del grupo) |
| Horario | texto | mañana / tarde / noche | **Dato**: `Departure_Hour` | No puede estar vacío |
| Salida desde hub | texto | Sí / No | **Dato**: `Major_Hub_Departure` | No puede estar vacío |
| Destino | texto | Nacional / Internacional | **Dato**: `International_Flight` | No puede estar vacío |
| Costo esperado (MXN) | decimal | pesos mexicanos por vuelo | **Simulado**: modelo Beta-binomial con capacidad y costos capturados arriba de la tabla | No se publica: el grupo tiene menos de 30 pasajeros |
| Diferencia vs. no sobrevender (MXN) | decimal | pesos mexicanos por vuelo | **Simulado**: costo sin sobreventa − costo con la sobreventa recomendada | Igual que arriba |
| Sobreventa recomendada | entero | boletos extra | **Simulado**: boletos extra con menor costo esperado | Igual que arriba |
| Pasajeros | entero | pasajeros | **Calculado**: conteo de filas del grupo | No aplica: siempre ≥ 30 |
| No-shows | entero | pasajeros | **Calculado**: suma de `No_Show` | 0 significa que nadie faltó (no es vacío) |
| Tasa de no-show | decimal | proporción 0–1 (se muestra en %) | **Calculado**: No-shows ÷ Pasajeros | No aplica: el denominador nunca es 0 |
| Probabilidad prevista | decimal | proporción 0–1 (se muestra en %) | **Calculado**: promedio de la probabilidad de la regresión logística | No aplica |

Las columnas de dinero son numéricas (no texto), así que se ordenan bien al hacer clic en su encabezado. La tabla usa `column_order` y `hide_index=True`.

## C. Cómo se distinguen en pantalla dato, calculado y simulado

- **Dato** (etiqueta gris sólida): sale tal cual del archivo o es una tasa observada.
- **Calculado** (etiqueta morada): fórmula o predicción del modelo.
- **Simulado** (etiqueta ámbar con borde punteado): escenario con supuestos de capacidad y costos.

En la tabla el origen va entre corchetes en el encabezado: `[dato]`, `[calculado]`, `[simulado]`.

## D. Itinerario de vuelos: `data/vuelos.csv` (calendario de Laura)

El archivo de pasajeros no trae número de vuelo, ruta ni fecha. El calendario usa la hoja **«Vuelos»** del Excel cargado; si no la trae, usa `data/vuelos.csv`. Es un **itinerario de referencia** (etiqueta **Simulado**) con aeropuertos reales y la configuración de asientos típica de cada avión, generado con `scripts/generar_itinerario.py`. Se reemplaza por el itinerario real con las mismas columnas. Lo revisa `core/flights.py`; si no cumple, el calendario muestra el problema en lugar de los vuelos.

| Columna | Tipo | Unidad / códigos | De dónde viene | Vacío significa |
|---|---|---|---|---|
| `vuelo` | texto | número de vuelo, único (ej. `AL 106`) | Itinerario | No se permite |
| `origen` / `destino` | texto | código IATA del aeropuerto | Itinerario | No se permite |
| `ciudad_origen` / `ciudad_destino` | texto | nombre de la ciudad | Itinerario | No se permite |
| `salida` | texto | hora local `HH:MM`; define el horario igual que `Departure_Hour` (6–12 mañana, 12–18 tarde, 18–6 noche) | Itinerario | No se permite |
| `dias` | texto | dígitos de los días que opera, 1 = lunes … 7 = domingo (ej. `12345`) | Itinerario | No se permite |
| `avion` | texto | modelo de avión | Itinerario | No se permite |
| `asientos` | entero | asientos, entre 20 y 600 | Itinerario | No se permite |
| `sale_de_hub` | entero | 0/1, como `Major_Hub_Departure` | Itinerario | No se permite |
| `internacional` | entero | 0/1, como `International_Flight` | Itinerario | No se permite |

**No-show previsto por vuelo (Calculado):** promedio de la probabilidad del modelo en los pasajeros de su misma combinación día × horario × hub × destino; si esa combinación tiene menos de 30 pasajeros, se usa día × horario. **Porcentaje de cada día del calendario (Dato):** tasa observada de no-show de ese día de la semana.

**Con `Flight_Date`:** cada día del calendario muestra la tasa observada de esa fecha y de cada horario (mañana, tarde, noche); si hay menos de 30 pasajeros no se publica (—). Las fechas sin pasajeros muestran el patrón de su día de la semana con borde punteado.
