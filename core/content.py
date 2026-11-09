"""Textos del producto: fichas metodológicas, glosario, perfiles, recorridos y objetivo de negocio."""

GLOSSARY = {
    "No-show": "Pasajero con boleto que no se presenta al vuelo (No_Show = 1).",
    "Sobreventa": "Vender más boletos que asientos, esperando que algunos pasajeros no se presenten.",
    "Costo esperado": "Promedio ponderado por probabilidad del costo de asientos vacíos más el de pasajeros sin asiento.",
    "AUC": "Probabilidad de que el modelo dé más riesgo a un pasajero que faltó que a uno que se presentó. 0.5 = azar, 1 = perfecto.",
    "Precision": "De los pasajeros marcados con alerta, qué parte realmente no se presentó.",
    "Recall": "De los pasajeros que no se presentaron, qué parte recibió alerta.",
    "Umbral": "Probabilidad a partir de la cual un pasajero recibe alerta.",
    "Falsa alarma": "Pasajero con alerta que sí se presentó.",
    "Calibración": "Qué tanto coincide la probabilidad prevista con la frecuencia real (ECE = error medio).",
    "IC 95%": "Rango donde probablemente está la tasa real dado el tamaño de la muestra (Wilson).",
    "PSI": "Índice de estabilidad: compara la distribución de una variable entre dos conjuntos de datos.",
}

PERSONAS = {
    "laura": {
        "nombre": "Laura", "rol": "Planificación",
        "pregunta": "¿Cuántos boletos adicionales conviene vender sin asumir un riesgo económico inaceptable?",
        "contexto": "Planifica capacidad y política de sobreventa por tipo de vuelo.",
        "conocimiento": "Domina operación y costos; no necesita detalle de modelos.",
        "necesidad": "Estimar ausentes y equilibrar asientos vacíos contra pasajeros sin asiento.",
        "frecuencia": "Al planear cada temporada o cambio de capacidad; consulta semanal.",
        "exito": "Propuesta de sobreventa preparada",
    },
    "armando": {
        "nombre": "Armando", "rol": "Experiencia del pasajero",
        "pregunta": "¿Qué pasajeros o segmentos requieren atención y qué intervención es la adecuada?",
        "contexto": "Diseña campañas de contacto y atención antes del vuelo.",
        "conocimiento": "Conoce al cliente y los canales; conocimiento básico de estadística.",
        "necesidad": "Priorizar segmentos y saber por qué requieren atención.",
        "frecuencia": "Diaria para listas de contacto; mensual para revisar segmentos.",
        "exito": "Segmento priorizado e intervención preparada",
    },
    "anna": {
        "nombre": "Anna", "rol": "Operación y calidad",
        "pregunta": "¿Los datos y el modelo son suficientemente confiables para usar las predicciones?",
        "contexto": "Responsable de la calidad de datos y del monitoreo del modelo.",
        "conocimiento": "Conocimiento técnico de datos y métricas de clasificación.",
        "necesidad": "Validar el corte, ajustar alertas y aceptar o bloquear su uso.",
        "frecuencia": "Antes de cada corte nuevo; diaria operativa; semanal de indicadores; completa al actualizar el modelo.",
        "exito": "Corte aceptado o bloqueado con razón",
    },
}

USER_TABLE = [
    {"Usuario": "Laura · Planificación", "Problema": "Asientos vacíos por no-show o pasajeros sin asiento por sobrevender de más.",
     "Decisión": "Cuántos boletos extra vender por tipo de vuelo.", "Alcance": "Simulación de escenario con tasas agregadas; no hay vuelos reales en el dataset."},
    {"Usuario": "Armando · Experiencia", "Problema": "Contactar a todos es caro; no contactar deja ausencias evitables.",
     "Decisión": "Qué segmento priorizar y con qué intervención.", "Alcance": "Reglas explícitas sobre variables del dataset; lista individual solo con autorización."},
    {"Usuario": "Anna · Operación y calidad", "Problema": "Usar predicciones con datos defectuosos o un modelo degradado.",
     "Decisión": "Aceptar o bloquear el corte y fijar el umbral de alerta.", "Alcance": "Validaciones reproducibles sobre el archivo cargado y la partición usada."},
]

SURVEILLANCE = [
    {"Momento": "Antes de usar cada corte nuevo", "Revisión": "Validación de datos completa (todas las reglas de calidad).", "Responsable": "Anna"},
    {"Momento": "Diariamente, si hay información nueva", "Revisión": "Revisión operativa: volumen, valores fuera de rango, tasa del día.", "Responsable": "Anna"},
    {"Momento": "Semanalmente", "Revisión": "Indicadores del modelo y alertas: AUC, recall, precision, PSI.", "Responsable": "Anna con Armando"},
    {"Momento": "Al actualizar el modelo", "Revisión": "Evaluación completa en validación y prueba; nueva aprobación del umbral.", "Responsable": "Anna con el equipo"},
]

JOURNEYS = [
    {"Persona": "Laura", "Recorrido": "Elige condiciones del vuelo → revisa riesgo → compara sobreventa → decide → propuesta preparada",
     "Datos insuficientes": "Grupo con n < 30: resultado no concluyente y botón para ampliar a todos los días del mismo horario.",
     "Error de cálculo": "Mensaje con la causa y botón para restablecer valores.",
     "Acceso restringido": "No aplica: usa solo agregados.",
     "No concluyente": "Ninguna sobreventa cumple la tolerancia de riesgo: se informa y se sugiere relajarla o revisar costos."},
    {"Persona": "Armando", "Recorrido": "Consulta segmentos → identifica riesgo → elige intervención → revisa prioridad → segmento priorizado",
     "Datos insuficientes": "Segmentos con n < 30 se ocultan con su motivo.",
     "Error de cálculo": "Mensaje y recuperación con el umbral recomendado.",
     "Acceso restringido": "Lista individual solo con rol Experiencia; sin él se muestra una demostración con pasajeros ficticios.",
     "No concluyente": "Sin pasajeros con alerta en el segmento: se sugiere bajar el umbral o elegir otro segmento."},
    {"Persona": "Anna", "Recorrido": "Revisa calidad → analiza métricas → ajusta umbral → acepta o bloquea el corte",
     "Datos insuficientes": "Segmentos de diagnóstico con menos de 10 positivos se marcan como inciertos.",
     "Error de cálculo": "Si el archivo no carga, el corte queda bloqueado con la causa.",
     "Acceso restringido": "Registrar la decisión requiere rol Operación; sin él se ve el estado calculado.",
     "No concluyente": "Advertencias sin falla crítica: aceptado con observaciones y acciones pendientes."},
]

DISCARDED = [
    {"Alternativa descartada": "Dispersión de pasajeros por día y hora",
     "Motivo": "Con variables categóricas, 10,000 puntos caen en 21 posiciones y se superponen; no se ve la tasa.",
     "Sustituida por": "Mapa de calor de tasas agregadas día × horario con su denominador."},
    {"Alternativa descartada": "Gráfica de pastel por segmento",
     "Motivo": "No permite comparar tasas entre segmentos de distinto tamaño ni mostrar el promedio.",
     "Sustituida por": "Barras horizontales ordenadas con línea del promedio, n e IC 95%."},
    {"Alternativa descartada": "Velocímetro (gauge) de probabilidad individual",
     "Motivo": "Ocupa espacio, se lee con poca precisión y no explica el porqué.",
     "Sustituida por": "Número con comparación contra el promedio y barras de contribución del modelo."},
]

BUSINESS_GOAL = [
    {"Elemento": "Objetivo", "Contenido": "Reducir el costo esperado del no-show (asientos vacíos + pasajeros sin asiento) con decisiones de sobreventa y contacto basadas en datos."},
    {"Elemento": "Línea base", "Contenido": "{baseline}"},
    {"Elemento": "Meta", "Contenido": "Propuestas pendientes de aprobación del equipo: (a) bajar 20% los asientos vacíos esperados por 100 asientos sin superar 10% de probabilidad de negar abordaje; (b) contactar al menos 60% de los no-shows con alerta (recall ≥ 0.60) con precision ≥ 0.55."},
    {"Elemento": "Indicadores", "Contenido": "Empresa: asientos vacíos y abordajes negados por vuelo, costo por vuelo. Modelo: recall, precision, calibración. Un AUC alto no prueba por sí solo una reducción de costos."},
    {"Elemento": "Decisión que habilita", "Contenido": "Política de sobreventa por tipo de vuelo (Laura), campañas de contacto (Armando) y uso operativo del corte (Anna)."},
]


def _f(nombre, pregunta, usuario, variables, tipo, porque, descartada, decision, limitaciones):
    return dict(nombre=nombre, pregunta=pregunta, usuario=usuario, variables=variables, tipo=tipo,
                porque=porque, descartada=descartada, decision=decision, limitaciones=limitaciones)


FICHAS = {
    "costos": _f("Costo esperado por boletos extra", "¿Con cuántos boletos extra el costo esperado es mínimo?", "Laura",
                 "Boletos extra (0…k), costo esperado en MXN, probabilidad de negar abordaje", "Línea con punto óptimo y zonas de riesgo",
                 "Los boletos extra tienen un orden continuo y la curva muestra el intercambio entre vacíos y negados.",
                 "Barras por cada k: ocultan la forma de la curva y el mínimo.",
                 "Elegir la sobreventa y ver cuánto cuesta desviarse del óptimo.",
                 "Simulación sobre tipos de vuelo aproximados; costos son entradas del usuario; supone que todos los boletos se venden."),
    "mapa": _f("Mapa de riesgo día × horario", "¿Qué combinaciones de día y horario tienen más no-show?", "Laura",
               "Departure_Day, Departure_Hour, No_Show (filtros: hub, destino)", "Mapa de calor de tasas agregadas",
               "Resume 21 combinaciones con su tasa y denominador sin superponer puntos.",
               "Dispersión de pasajeros individuales: superposición masiva (Bloque B).",
               "Detectar dónde revisar la política de sobreventa.",
               "Tasas históricas observadas; grupos con n < 30 suprimidos; no implica causa."),
    "top": _f("Combinaciones con mayor tasa histórica", "¿Qué tipos de vuelo concentran más ausencias?", "Laura",
              "Día, horario, hub, destino, No_Show", "Tabla ordenada con n, ausencias, tasa e IC 95%",
              "Necesita valores exactos y denominadores para comparar.", "Ranking solo por tasa sin n: confunde grupos pequeños con evidencia sólida.",
              "Elegir qué tipo de vuelo simular primero.", "Una tasa alta no es por sí misma una recomendación de sobrevender."),
    "segmentos": _f("Tasa observada por segmento", "¿Qué segmentos faltan más que el promedio?", "Armando",
                    "Clase, compra, viajero frecuente, negocios, conexión, clima, destino, horario; No_Show",
                    "Barras horizontales ordenadas con línea del promedio",
                    "Comparación directa entre segmentos con etiqueta de valor, n y diferencia en puntos.",
                    "Pastel por segmento: no compara tasas de grupos de distinto tamaño.",
                    "Elegir segmentos a intervenir.", "Asociación histórica, no causa; los segmentos se traslapan."),
    "importancia": _f("Peso de cada variable en el modelo", "¿Qué variables usa más el modelo para separar el riesgo?", "Armando, Anna",
                      "Coeficientes de la regresión logística (rango por variable)", "Barras horizontales ordenadas",
                      "Muestra la importancia del modelo, distinta de la tasa observada.", "Tabla de coeficientes: difícil de comparar a simple vista.",
                      "Entender qué información pesa en las alertas.", "Importancia en log-odds; no es efecto causal."),
    "contrib": _f("Factores del pasajero", "¿Qué sube o baja el riesgo de este perfil?", "Armando",
                  "Contribución en log-odds de cada variable frente al pasajero promedio de entrenamiento", "Barras divergentes",
                  "En una regresión logística la contribución es exacta y suma la diferencia frente al promedio.",
                  "Velocímetro de probabilidad: no explica el porqué.", "Elegir la intervención según el factor dominante.",
                  "Explica al modelo, no la realidad del pasajero; correlación, no causa."),
    "modelos": _f("Comparación de modelos", "¿Qué modelo separa mejor y es confiable?", "Anna",
                  "AUC, precision, recall, F1, KS, Brier, ECE por modelo y partición", "Tabla + puntos de AUC con IC 95%",
                  "Métricas exactas por partición y la incertidumbre de la diferencia.",
                  "Barras de AUC desde cero: diferencias de milésimas parecen iguales o se exageran al truncar.",
                  "Elegir el modelo con evidencia, no por una diferencia mínima.", "IC por bootstrap sobre 1,000 pasajeros de prueba."),
    "calibracion": _f("Calibración", "¿Las probabilidades coinciden con lo que pasó?", "Anna, Laura",
                      "Probabilidad media prevista y tasa real por rango de probabilidad (prueba)", "Puntos sobre diagonal",
                      "La diagonal es la referencia directa de calibración perfecta.", "Histograma de probabilidades: no compara con la realidad.",
                      "Decidir si el simulador puede sumar probabilidades.", "Rangos con pocos pasajeros son inestables (se muestra n)."),
    "umbral": _f("Intercambio de umbral", "¿Cuántos no-shows detecto y cuántas falsas alarmas genero?", "Anna, Armando",
                 "Recall, precision y % de alertas por umbral", "Líneas por umbral con marcador del valor elegido",
                 "El umbral es continuo y la gráfica muestra el intercambio.", "Curva ROC: no muestra el umbral ni las falsas alarmas en conteos.",
                 "Fijar el umbral de alerta.", "Depende de la partición elegida; prueba se usa solo para evaluar."),
    "matriz": _f("Matriz de confusión", "¿Cómo se reparten los pasajeros con el umbral elegido?", "Anna",
                 "Verdaderos/falsos positivos y negativos", "Matriz 2×2 con conteos",
                 "Conteos exactos que suman el total evaluado.", "Solo porcentajes: ocultan el tamaño del conjunto.",
                 "Validar el costo operativo de las alertas.", "Corresponde solo a la partición indicada."),
    "diagnostico": _f("Diagnóstico por segmento", "¿Dónde funciona bien el modelo y dónde es incierto?", "Anna",
                      "AUC y recall por segmento en prueba, n y positivos", "Tabla con estado de confianza",
                      "Valores exactos con su base.", "Mapa de calor: sugiere precisión donde hay pocos positivos.",
                      "Decidir dónde usar alertas con cautela.", "Segmentos con menos de 10 positivos se marcan inciertos."),
    "psi": _f("Estabilidad (PSI)", "¿Cambiaron las distribuciones entre entrenamiento y evaluación?", "Anna",
              "Distribución de cada variable en entrenamiento vs. validación+prueba", "Tabla con estado",
              "Pocas variables; los valores exactos importan.", "Gráfica de distribuciones por variable: demasiadas gráficas.",
              "Vigilar degradación y decidir reentrenar.", "Sin fechas no se puede medir deriva en el tiempo, solo entre particiones."),
}
