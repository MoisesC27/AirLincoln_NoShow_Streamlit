# Contrato del prompt — Equipo 4

## Qué debe mostrar

Nuestro producto es un dashboard interactivo desarrollado en Streamlit para **Air Lincoln**. Su propósito es ayudar a tomar decisiones relacionadas con el No-show y la sobreventa de vuelos usando la información histórica disponible del equipo.

La idea no es mostrar únicamente gráficas o indicadores, sino permitir que un usuario pueda plantear un escenario de vuelo, observar el riesgo asociado y entender qué decisión podría tomar a partir de los resultados.

El dashboard parte de un conjunto de **10,000 pasajeros históricos** y debe mostrar de forma clara el comportamiento del No-show, los factores que pueden modificar el riesgo y el impacto económico de vender más boletos que los asientos disponibles.

### Usuarios del dashboard

El cliente principal del producto es **Air Lincoln**, pero dentro de la aerolínea identificamos tres perfiles de usuario con necesidades diferentes.

**Laura — Planificación**

Laura representa al área encargada de planear la capacidad de los vuelos. Su principal interés es decidir **cuántos boletos adicionales conviene vender** sin aumentar demasiado el riesgo de dejar pasajeros sin asiento.

Para ella, el dashboard debe mostrar principalmente:

- sobreventa recomendada;
- número total de boletos frente a los asientos disponibles;
- probabilidad estimada de No-show;
- costo esperado;
- ahorro frente a no aplicar sobreventa;
- riesgo de negar abordaje.

La decisión que habilita para este perfil es:

**¿Cuántos boletos adicionales conviene vender bajo las condiciones actuales del vuelo?**

---

**Armando — Experiencia del pasajero**

Armando representa al área de experiencia del pasajero. Su interés no es únicamente aumentar el aprovechamiento del vuelo, sino entender qué impacto puede tener una decisión de sobreventa sobre los clientes.

Para este usuario es importante observar:

- riesgo de que algún pasajero no tenga asiento;
- escenarios en los que la sobreventa deja de ser conveniente;
- cambios en el riesgo cuando se modifican las condiciones del vuelo;
- posibles costos asociados con negar abordaje.

La decisión que habilita para este perfil es:

**¿El beneficio de vender boletos adicionales justifica el riesgo que se está generando para el pasajero?**

Además, cuando la decisión operativa requiere identificar a una persona concreta, Armando puede consultar una vista priorizada de pasajeros con mayor riesgo.

Esta vista muestra únicamente la información necesaria para realizar una acción:

- identificador del pasajero;
- probabilidad estimada de No-show;
- principal motivo de riesgo;
- acción preventiva sugerida.

La información individual se utiliza únicamente cuando la acción requiere identificar al pasajero. Para el análisis general del producto se mantienen resultados agregados.

Esta vista permite responder una decisión adicional:

**¿A qué pasajeros conviene contactar primero y qué acción preventiva debería realizarse?**

---

**Anna — Operación y calidad**

Anna representa al área de operación y calidad. Su función es revisar si la recomendación es razonable considerando las condiciones reales del vuelo y detectar escenarios que requieren mayor atención.

Para este perfil, el dashboard debe facilitar la revisión de factores como:

- día y horario del vuelo;
- salida desde un hub;
- tipo de destino;
- condiciones climáticas;
- comportamiento histórico del No-show;
- nivel de riesgo del escenario seleccionado.

La decisión que habilita para este perfil es:

**¿Las condiciones operativas del vuelo hacen recomendable mantener la estrategia propuesta o requieren una revisión adicional?**

---

## Componentes principales del dashboard

La primera pantalla debe funcionar como un **simulador de sobreventa**.

El usuario podrá configurar un vuelo mediante:

- día del vuelo;
- horario;
- salida desde un hub;
- tipo de destino;
- pronóstico del clima;
- número de asientos disponibles;
- costo estimado de un asiento vacío;
- costo asociado con negar abordaje.

Al modificar estos valores, el dashboard debe actualizar los resultados del escenario.

Los principales resultados que debe mostrar son:

- cantidad recomendada de boletos adicionales;
- total de boletos que se venderían;
- porcentaje estimado de pasajeros que no llegarán;
- riesgo de dejar a algún pasajero sin asiento;
- ahorro esperado frente a una estrategia sin sobreventa;
- costo esperado para distintos niveles de sobreventa.

Además del simulador, el producto debe incluir un **mapa de riesgo** que permita observar y comparar escenarios para entender en qué condiciones una estrategia puede ser más o menos conveniente.

La decisión general que habilita el producto es:

**¿Qué nivel de sobreventa ofrece el mejor equilibrio entre aprovechar la capacidad del vuelo, reducir el costo de asientos vacíos y mantener controlado el riesgo para los pasajeros?**

---

## El diseño de lo que debe arrojar

La información debe presentarse de manera que el usuario pueda comprender primero la recomendación y después revisar por qué se obtuvo.

En la parte superior debe aparecer la recomendación principal:

1. **Sobreventa recomendada**, expresada en boletos adicionales.
2. **Boletos totales**, comparados con la cantidad de asientos disponibles.

Debajo deben mostrarse los indicadores que ayudan a evaluar la recomendación:

3. **Pasajeros que probablemente no llegarán**, expresado como porcentaje.
4. **Riesgo de dejar a alguien sin asiento**, expresado como porcentaje.
5. **Ahorro esperado**, expresado en MXN.

Después debe aparecer una gráfica de análisis económico.

### Gráfica de costo esperado

La gráfica debe utilizar:

- **Eje X:** cantidad de boletos adicionales.
- **Eje Y:** costo esperado en MXN.

También debe mostrar:

- zona de riesgo bajo;
- zona de riesgo medio;
- zona de riesgo alto;
- punto recomendado;
- costo esperado para cada nivel de sobreventa.

La recomendación debe quedar resaltada visualmente para que el usuario pueda identificarla sin tener que interpretar toda la gráfica.

Finalmente, el dashboard debe permitir consultar el **mapa de riesgo**, donde se puedan comparar diferentes condiciones del vuelo y detectar escenarios que requieren mayor atención.

---

## Objetivo de negocio

La situación base consiste en operar el vuelo sin utilizar una recomendación analítica de sobreventa, lo que puede provocar que algunos asientos queden vacíos cuando pasajeros con reservación no se presentan.

La meta del producto es utilizar la información histórica de No-show para encontrar un mejor equilibrio entre el aprovechamiento de la capacidad del vuelo y el riesgo de vender más boletos que los asientos disponibles.

No buscamos eliminar completamente el riesgo, sino hacerlo visible y permitir que el usuario compare el beneficio económico con las posibles consecuencias para el pasajero.

La decisión principal que habilita el dashboard es determinar **cuántos boletos adicionales vender para un vuelo específico considerando sus condiciones y costos**.

---

## El prompt, literal

Desarrolla un dashboard interactivo en Streamlit para Air Lincoln utilizando un dataset de 10,000 pasajeros históricos.

El producto debe apoyar decisiones relacionadas con No-show y sobreventa de vuelos. No debe limitarse a mostrar gráficas descriptivas; debe permitir que el usuario configure un escenario y obtenga una recomendación clara.

El dashboard debe considerar tres perfiles de usuario:

- Planificación, que necesita decidir cuántos boletos adicionales vender.
- Experiencia del pasajero, que necesita evaluar el riesgo de afectar a pasajeros por una sobreventa.
- Operación y calidad, que necesita revisar si las condiciones operativas del vuelo hacen razonable la recomendación.

La pantalla principal debe funcionar como un simulador de sobreventa.

Permite seleccionar:

- día;
- horario;
- salida desde un hub;
- destino nacional o internacional;
- pronóstico del clima;
- número de asientos;
- costo de un asiento vacío;
- costo de negar abordaje.

A partir de estas entradas, muestra:

- sobreventa recomendada;
- boletos totales frente a asientos disponibles;
- porcentaje estimado de pasajeros que no llegarán;
- riesgo de dejar a alguien sin asiento;
- ahorro esperado frente a no aplicar sobreventa.

Incluye una gráfica de costo esperado según la cantidad de boletos adicionales. El eje X debe representar boletos adicionales y el eje Y costo esperado en MXN.

La gráfica debe diferenciar visualmente zonas de riesgo bajo, medio y alto y marcar la recomendación encontrada.

Agrega también un mapa de riesgo para comparar escenarios y entender qué combinaciones de condiciones presentan mayor riesgo.

La interfaz debe ser clara, compacta y orientada a la toma de decisiones. La recomendación debe aparecer primero y después la información necesaria para entender y evaluar esa recomendación.

El objetivo final es que el usuario pueda responder:

**¿Cuántos boletos adicionales conviene vender y qué riesgo implica hacerlo?**

---

## Qué devolvió

El modelo generó una primera propuesta funcional del dashboard con un simulador de sobreventa, controles para configurar las condiciones del vuelo, indicadores de riesgo y costo, una recomendación de boletos adicionales y una gráfica para comparar distintos niveles de sobreventa.

También propuso una organización visual para presentar primero la recomendación y después los elementos utilizados para evaluarla.

---

## Qué cambiamos de lo que devolvió

A partir de la primera versión realizamos cambios para que el producto estuviera más relacionado con el problema específico de Air Lincoln y con las decisiones que buscamos apoyar.

Ajustamos la organización de la pantalla, los textos, la forma de presentar la recomendación, los niveles de riesgo y los costos.

También incorporamos y refinamos los controles utilizados para representar las condiciones del vuelo y revisamos qué información era realmente útil para cada perfil de usuario.

El equipo decidió conservar una vista principal enfocada en el simulador de sobreventa y una vista adicional para analizar el riesgo de distintos escenarios.

---

## Qué decidimos nosotros y no el modelo

El equipo definió el objetivo final del producto y la forma en que debía utilizarse dentro del contexto de Air Lincoln.

Nosotros decidimos:

- que la decisión principal sería determinar cuántos boletos adicionales vender;
- que el producto debía considerar tanto el beneficio económico como el riesgo para el pasajero;
- que existirían tres perfiles principales de usuario: Planificación, Experiencia del pasajero y Operación y calidad;
- qué variables del proyecto eran relevantes para configurar un escenario;
- qué costos utilizar en el simulador;
- cómo interpretar los niveles de riesgo;
- qué resultados debían mostrarse primero;
- qué información debía aparecer en cada vista;
- qué elementos de las propuestas del modelo conservar, modificar o eliminar.

El modelo se utilizó como apoyo para construir y revisar la primera iteración, pero las decisiones sobre el significado del producto, los usuarios, las variables y la forma final del dashboard fueron tomadas por el equipo.
### Ficha de las visualizaciones

**Costo esperado por boletos extra**

- **Pregunta que responde:** ¿qué cantidad de boletos adicionales produce el menor costo esperado para las condiciones seleccionadas?
- **Alternativa descartada:** mostrar únicamente una tabla de costos.
- **Razón:** la gráfica permite comparar rápidamente diferentes niveles de sobreventa, identificar el punto recomendado y observar cuándo aumenta el riesgo.

**Mapa de riesgo**

- **Pregunta que responde:** ¿qué combinaciones de condiciones presentan mayor riesgo y requieren una revisión adicional?
- **Alternativa descartada:** gráfica de dispersión con observaciones individuales.
- **Razón:** el análisis exploratorio mostró una gran concentración y superposición de registros en pocas combinaciones. Trabajar con información agregada permite comparar los escenarios con mayor claridad y evita exponer registros individuales.

**Indicadores de recomendación, No-show, riesgo y ahorro**

- **Pregunta que responden:** ¿cuál es la recomendación actual y cuáles son sus principales consecuencias operativas y económicas?
- **Alternativa descartada:** presentar estos resultados únicamente dentro de una tabla.
- **Razón:** los indicadores permiten identificar primero la decisión y después profundizar en la gráfica para comprender el comportamiento del costo y el riesgo.