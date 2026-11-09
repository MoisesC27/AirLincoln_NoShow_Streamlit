# Registro de prompts — Equipo 4

## Bloque 1 — Primera iteración del dashboard

### Prompt 1

**Etapa SDLC:** Planeación y diseño

**Objetivo:** definir qué problema debía resolver el dashboard, qué información debía mostrar y qué decisión debía permitir tomar.

**Prompt utilizado:**

> Ayúdame a definir la primera versión de un dashboard en Streamlit para Air Lincoln utilizando un dataset histórico de pasajeros y No-show. El producto debe permitir analizar la sobreventa de vuelos y ayudar a decidir cuántos boletos adicionales vender considerando el riesgo para el pasajero y el costo esperado.
>
> El dashboard debe estar pensado para tres perfiles: Planificación, Experiencia del pasajero y Operación y calidad. Propón qué información necesita cada usuario, qué controles debe tener el dashboard y qué resultados deberían mostrarse.

**Qué devolvió:**

El modelo propuso una estructura inicial del producto con controles para configurar un vuelo, indicadores relacionados con No-show, costos y riesgo, así como una recomendación de sobreventa.

También sugirió organizar la información de acuerdo con las necesidades de diferentes usuarios.

**Qué verificamos:**

Revisamos que las variables propuestas tuvieran relación con el dataset y con el problema trabajado durante el proyecto.

También verificamos que la recomendación principal estuviera relacionada con una decisión que realmente pudiera tomar un usuario de Air Lincoln.

**Qué cambiamos de lo que devolvió:**

Reducimos la cantidad de información mostrada en la vista principal y priorizamos los resultados necesarios para tomar una decisión.

También modificamos los perfiles de usuario y la forma de presentar los indicadores para que fueran consistentes con nuestro proyecto.

**Qué decidimos nosotros y no el modelo:**

El equipo decidió que el objetivo principal del producto sería responder:

**¿Cuántos boletos adicionales conviene vender para un vuelo específico?**

También decidimos utilizar tres perfiles principales:

- Laura — Planificación.
- Armando — Experiencia del pasajero.
- Anna — Operación y calidad.

El equipo definió qué significado tendría cada perfil y qué decisiones debía poder tomar dentro del dashboard.

---

### Prompt 2

**Etapa SDLC:** Implementación

**Objetivo:** construir una primera versión funcional del dashboard en Streamlit a partir del diseño planteado.

**Prompt utilizado:**

> Desarrolla una primera versión funcional en Streamlit del dashboard de Air Lincoln.
>
> La pantalla principal debe funcionar como un simulador de sobreventa y permitir seleccionar día, horario, salida desde un hub, tipo de destino y pronóstico del clima.
>
> También debe permitir introducir el número de asientos, el costo de un asiento vacío y el costo de negar abordaje.
>
> Muestra una recomendación de boletos adicionales, pasajeros que probablemente no llegarán, riesgo de dejar a alguien sin asiento y ahorro esperado.
>
> Incluye una gráfica donde el eje X represente boletos adicionales y el eje Y el costo esperado en MXN. Diferencia visualmente zonas de riesgo bajo, medio y alto y marca la recomendación encontrada.

**Qué devolvió:**

El modelo generó una estructura inicial para implementar el simulador en Streamlit, incluyendo controles, indicadores y una visualización del costo esperado.

**Qué verificamos:**

Ejecutamos la aplicación localmente y comprobamos que los controles modificaran los resultados.

También revisamos que las unidades, costos, porcentajes y cantidad de boletos fueran comprensibles para un usuario.

**Qué cambiamos de lo que devolvió:**

Se reorganizó la interfaz para mostrar primero la recomendación de sobreventa y después los indicadores de riesgo y costo.

También se modificó la gráfica para destacar el punto recomendado y diferenciar las zonas de riesgo.

**Qué decidimos nosotros y no el modelo:**

El equipo decidió la jerarquía final de la pantalla, qué indicadores serían prioritarios y cómo debía interpretarse una recomendación de sobreventa.

También decidimos que el producto no debía mostrar solamente una predicción, sino ayudar a comparar el beneficio económico contra el riesgo para el pasajero.

---

### Prompt 3

**Etapa SDLC:** Pruebas y revisión

**Objetivo:** revisar la primera iteración y detectar mejoras antes de publicar el dashboard.

**Prompt utilizado:**

> Revisa esta primera versión del dashboard de Air Lincoln como si fueras un usuario de negocio. Identifica problemas de claridad, jerarquía visual, interpretación de indicadores y facilidad para tomar la decisión de cuántos boletos adicionales vender.
>
> No cambies el objetivo del producto. Propón únicamente mejoras que hagan más clara la decisión.

**Qué devolvió:**

El modelo sugirió mejorar la jerarquía de los indicadores, aclarar algunos títulos, separar mejor los controles de entrada de los resultados y hacer más visible la recomendación principal.

**Qué verificamos:**

El equipo revisó cada sugerencia y comparó las propuestas con el objetivo original y con la retroalimentación recibida durante la presentación del proyecto.

**Qué cambiamos de lo que devolvió:**

Se conservaron únicamente las recomendaciones que mejoraban la lectura del producto sin modificar la lógica definida por el equipo.

Se ajustaron textos, tamaños, distribución de componentes y la forma de presentar el riesgo y el ahorro esperado.

**Qué decidimos nosotros y no el modelo:**

El equipo decidió qué recomendaciones aplicar y cuáles descartar.

La versión final de esta primera iteración, los valores mostrados, los perfiles de usuario y la decisión habilitada por el dashboard fueron definidos y revisados por el equipo.