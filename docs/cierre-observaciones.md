# Cierre de observaciones de la exposición

## Retroalimentación de la exposición del 21 de octubre — Equipo 4

La retroalimentación correspondiente a la exposición del 21 de octubre fue publicada por el profesor el 28 de octubre de 2026. A partir de esos comentarios revisamos qué elementos de nuestra propuesta ya funcionaban, cuáles debían mantenerse y qué puntos necesitaban hacerse más explícitos en la primera versión funcional del dashboard de Air Lincoln.

El objetivo no fue cambiar por completo el diseño presentado, sino llevarlo a una aplicación funcional en Streamlit y cerrar las observaciones pendientes sin perder las decisiones que ya habían sido justificadas durante la exposición.

| Bloque | Retroalimentación recibida | Qué hicimos en la primera iteración | Dónde quedó |
|---|---|---|---|
| **A — Usuarios, problema, decisión y alcance** | La definición de usuarios, problema, decisión y alcance fue correcta. El punto pendiente fue que la frecuencia de vigilancia de **Anna** quedaba implícita y no tenía un intervalo declarado. | Conservamos los tres perfiles y desarrollamos funciones distintas para cada uno. En el caso de **Anna — Operación y calidad**, su participación ya no se limita a una descripción del rol: cuenta con vistas para revisar la confiabilidad del modelo, ajustar el umbral de alertas y evaluar la calidad de los datos. También hicimos explícita su frecuencia de revisión: debe realizarse **por cada escenario o vuelo analizado antes de aceptar una recomendación operativa**, además de repetirse cuando cambie el dataset o se detecten variaciones relevantes en la calidad o desempeño del modelo. | Perfil **Anna — Operación y calidad**. Pestañas **¿El modelo es confiable?**, **Ajustar alertas** y **Calidad de datos**. La frecuencia también se documenta en `contrato-prompt.md`. |
| **B — Alternativas de diseño** | Las tres alternativas descartadas estaban justificadas. También se valoró correctamente haber reemplazado la dispersión por día y horario por una representación basada en tasas y bases por combinación, debido a la superposición de observaciones encontrada en el EDA. | Conservamos el criterio de trabajar con información agregada y evitamos presentar registros individuales de pasajeros cuando no aportan directamente a la decisión. La aplicación actual prioriza tasas, probabilidades, costos, escenarios y resultados agregados. Esto facilita la interpretación y reduce la exposición innecesaria de información individual. | Diseño general del dashboard, **Simulador de sobreventa**, **Mapa de riesgo**, indicadores agregados y visualizaciones de los perfiles. |
| **C — Recorridos y estados de éxito/error** | Cada recorrido terminaba en un estado de éxito distinto, pero la bifurcación de error aparecía únicamente en la pantalla de estado sin datos y no dentro del recorrido. | El recorrido funcional se planteó para que el usuario pueda regresar a los controles y modificar las entradas cuando un escenario no permita obtener una recomendación válida. De esta forma, el estado de error no representa un punto final: forma parte del proceso de recuperación y permite regresar a un escenario evaluable. Los estados de éxito siguen siendo diferentes según el perfil y la decisión que necesita tomar cada usuario. | Flujo de interacción del dashboard, controles del escenario y estados de recuperación de la aplicación. |
| **D — Justificación de visualizaciones** | La decisión de reemplazar la dispersión por tasas agregadas estaba bien argumentada y se conservaba el denominador visible. El faltante fue documentar para el resto de las visualizaciones **qué pregunta responde cada gráfica y qué alternativa fue descartada**. | En esta primera iteración relacionamos cada visualización principal con una pregunta concreta de negocio y documentamos por qué fue elegida. Por ejemplo, la gráfica de costo esperado responde qué nivel de sobreventa minimiza el costo esperado; el mapa de riesgo permite identificar escenarios que requieren más atención; la comparación de modelos permite revisar si el modelo seleccionado sigue siendo competitivo; la gráfica de probabilidades permite evaluar si las predicciones coinciden con la realidad; y la curva de alertas permite observar el intercambio entre detectar No-shows y generar falsas alarmas. | Visualizaciones de **Laura**, **Armando** y **Anna**, además de la sección de fichas de visualización incluida en `contrato-prompt.md`. |
| **E — Filtros y estados** | Los filtros estaban relacionados con la decisión, el estado por defecto mostraba el corte activo y los registros utilizados, y el estado sin datos incluía mensaje y acción de recuperación. | Conservamos esta lógica en la implementación. Los filtros de día, horario, salida desde un hub, destino y clima modifican directamente el escenario evaluado. También se conservaron los parámetros operativos de asientos, costo de asiento vacío y costo de negar abordaje, porque afectan directamente la recomendación de sobreventa. | Panel de configuración del **Simulador de sobreventa** y controles utilizados para modificar el escenario. |
| **F — Seguridad y autorización** | La propuesta de autenticación mediante OIDC, autorización mediante matriz de permisos, tratamiento de datos y supresión de celdas pequeñas fue evaluada correctamente. También se reconoció que no se permitía la exportación de registros individuales. | En la primera versión pública mantuvimos el principio de trabajar principalmente con información agregada y evitamos exponer registros individuales de pasajeros. Los perfiles de Laura, Armando y Anna continúan separados de acuerdo con las necesidades de cada rol. La versión publicada se utiliza como prototipo académico; los controles de autenticación y autorización descritos para un ambiente productivo permanecen documentados como parte del diseño de seguridad. | Perfiles **Laura, Armando y Anna**, resultados agregados del dashboard y documentación del producto. |

## Cierre específico de las observaciones pendientes

### Bloque A — Frecuencia de vigilancia de Anna

En la exposición original, el papel de Anna como responsable de operación y calidad estaba definido, pero no habíamos indicado con qué frecuencia debía realizar la revisión.

En la primera iteración funcional hicimos más concreto su recorrido. Anna puede revisar:

- la capacidad del modelo para distinguir pasajeros con mayor riesgo;
- la cantidad de No-shows detectados;
- la cantidad de alertas correctas;
- si las probabilidades estimadas coinciden con los resultados reales;
- el efecto de cambiar el umbral de alerta;
- los No-shows detectados y los que se escapan;
- las falsas alarmas;
- la calidad y estabilidad de los datos;
- las variables que todavía harían falta para utilizar el modelo por vuelo real.

La frecuencia de revisión queda definida de la siguiente manera:

**Anna debe realizar la revisión por cada escenario o vuelo analizado antes de aceptar una recomendación operativa. También debe repetirla cuando se actualicen los datos o cuando exista evidencia de cambios relevantes en la calidad o desempeño del modelo.**

De esta manera, la vigilancia deja de quedar implícita y pasa a formar parte explícita del uso del producto.

---

### Bloque D — Fichas de las visualizaciones

Para atender la observación relacionada con la justificación de las gráficas, documentamos la pregunta que responde cada una y la alternativa que fue descartada.

#### Costo esperado por boletos extra

**Pregunta que responde:**  
¿Cuántos boletos adicionales conviene vender para obtener el menor costo esperado bajo las condiciones seleccionadas?

**Alternativa descartada:**  
Mostrar únicamente una tabla con el costo asociado a cada cantidad de boletos.

**Por qué se descartó:**  
La gráfica permite identificar de forma más rápida el punto recomendado y observar cómo cambia el costo cuando se incrementa la sobreventa. También facilita distinguir las zonas de riesgo bajo, medio y alto.

---

#### Mapa de riesgo

**Pregunta que responde:**  
¿Qué combinaciones de condiciones presentan mayor riesgo y requieren una revisión adicional?

**Alternativa descartada:**  
Una gráfica de dispersión con observaciones individuales.

**Por qué se descartó:**  
Durante el EDA observamos una concentración importante de registros en pocas combinaciones, lo que provocaba superposición de puntos. La representación agregada facilita la comparación de escenarios y evita exponer pasajeros individuales.

---

#### Comparación de modelos

**Pregunta que responde:**  
¿El modelo seleccionado mantiene un desempeño competitivo frente a las demás alternativas?

**Alternativa descartada:**  
Presentar únicamente una tabla con las métricas de cada modelo.

**Por qué se descartó:**  
La comparación mediante barras permite reconocer rápidamente las diferencias entre modelos y ubicar la Regresión Logística frente a Gradient Boosting, Red Neuronal, Random Forest y Árbol de Decisión.

---

#### Probabilidades previstas contra resultados reales

**Pregunta que responde:**  
¿Las probabilidades que genera el modelo se parecen a lo que realmente ocurre?

**Alternativa descartada:**  
Mostrar solamente una métrica promedio de calibración.

**Por qué se descartó:**  
Comparar visualmente lo previsto con lo observado permite detectar en qué grupos de probabilidad el modelo se encuentra cerca de la realidad y en cuáles presenta diferencias.

---

#### Detectados contra falsas alarmas

**Pregunta que responde:**  
¿Qué ocurre con la capacidad de detectar No-shows cuando modificamos el umbral de alerta?

**Alternativa descartada:**  
Utilizar un único umbral fijo sin permitir comparar otras posibilidades.

**Por qué se descartó:**  
El objetivo de Anna es evaluar la calidad operativa de la alerta. La visualización permite entender el intercambio entre detectar una mayor proporción de No-shows y generar más falsas alarmas antes de aceptar un corte.

---

#### Indicadores principales

**Pregunta que responden:**  
¿Cuál es el resultado más importante del escenario actual y cuáles son sus principales consecuencias?

**Alternativa descartada:**  
Mostrar todos los valores únicamente dentro de una tabla.

**Por qué se descartó:**  
Los indicadores permiten identificar primero la recomendación, el riesgo, el costo y otros resultados clave sin obligar al usuario a leer una tabla completa antes de tomar una decisión.

---

## Resultado de los cambios

La retroalimentación recibida durante la exposición sirvió como punto de partida para pasar de un diseño conceptual a una primera versión funcional del dashboard.

Los tres perfiles mantienen objetivos diferentes:

- **Laura — Planificación:** utiliza el simulador para analizar cuántos boletos adicionales conviene vender y qué efecto económico tendría la decisión.
- **Armando — Experiencia del pasajero:** analiza el impacto que una estrategia puede generar sobre los pasajeros y el riesgo asociado con negar abordaje.
- **Anna — Operación y calidad:** revisa si el modelo y los datos son suficientemente confiables, analiza el efecto de los umbrales y detecta situaciones que deberían revisarse antes de utilizar una recomendación.

También se conservaron las decisiones que habían sido evaluadas positivamente durante la exposición: trabajar con resultados agregados, evitar exposición innecesaria de pasajeros individuales, mantener visibles las bases utilizadas para interpretar tasas y relacionar cada filtro con una decisión concreta.

La primera iteración ya no presenta únicamente resultados del análisis. El usuario puede configurar un escenario, evaluar sus consecuencias y utilizar la información para apoyar una decisión concreta dentro del contexto de Air Lincoln.