# Investigación · El ciclo de desarrollo con un asistente (Parte 1)

Referencia: Anthropic, *The AI-native SDLC playbook*, Claude Academy (14 lecciones), y la entrada de blog oficial que lo resume
(https://claude.com/blog/the-ai-native-sdlc-playbook). Lecciones leídas: Introducción y Test (también Build).

> **Borrador.** El equipo debe revisarlo, completar la pregunta 3 con su propia lectura y ajustar la redacción antes de entregar.

## 1. ¿En qué etapas del ciclo ya usamos el asistente y en cuáles no?

Lo contestamos revisando nuestros prompts (`prompts/`), no de memoria.

| Etapa | ¿Lo usamos? | Evidencia en nuestros prompts |
|---|---|---|
| **Plan** | Sí | 5 nov: «Necesito hacer un dashboard… con 3 usuarios… dime qué podría hacer… dime si me harían falta algunos datos». Se usó para capturar intención y detectar datos faltantes (número de vuelo, capacidad, tarifa). |
| **Design** | Sí, mucho | 8 nov: el «prompt maestro» con personas, decisiones, recorridos y requisitos del profesor. 9 nov: «no quiero fondo negro… que sea más parecido al primero». Iteramos el diseño con capturas. |
| **Build** | Sí, casi todo | El código de Streamlit, el simulador, el Excel con fórmulas y la plantilla los escribió el asistente. |
| **Test** | Parcialmente | Las pruebas existieron (pytest, simulación Monte Carlo para comprobar el +36 / 17.1%, capturas en celular), pero **las pidió el asistente por su cuenta o el prompt maestro**; nosotros nunca pedimos una prueba concreta ni la corrimos en el pipeline. |
| **Deploy** | No | Solo pedimos ayuda para correr la app localmente (errores de `venv` y de `python`). No hubo pull requests ni revisiones automáticas. |
| **Maintain** | No | No medimos si el tablero se usa ni si las decisiones mejoran. |

**Conclusión:** como dice el curso, usamos el asistente sobre todo para *escribir* (Build) y para *diseñar*. Test y Deploy, las etapas donde se detienen los errores, casi no las usamos. Un ejemplo: la versión anterior del tablero mezclaba métricas de prueba con las de validación + prueba, y nadie lo detectó hasta que se pidió una auditoría.

## 2. ¿Qué práctica concreta del curso podemos adoptar esta semana?

**«Darle al asistente una forma de comprobar su propio trabajo» y hacer que la verificación sea parte de "terminado".** El curso propone escribir en el `CLAUDE.md` cada comando de verificación junto con un ejemplo de salida sana, y escribir primero una prueba que falla antes de corregir un error.

Lo aplicamos así:
- `scripts/validar_datos.py` revisa el CSV contra el contrato y `python -m pytest -q` corre 15 pruebas. Ambos comandos están en `CLAUDE.md` con su salida esperada.
- Las pruebas de `tests/test_contract.py` se escribieron rompiendo el archivo a propósito (texto en `Booking_Class`, código 9 en `Departure_Day`, columna faltante) **antes** de dar por buena la validación.

También tomamos la distinción del curso entre control *orientativo* y control *determinista*: el `CLAUDE.md` y las skills hacen *probable* que el asistente siga una regla, pero nada lo obliga. Una regla que **siempre** debe cumplirse necesita un hook o una verificación en CI que bloquee el cambio.

## 3. ¿Qué esperábamos encontrar en el curso y no estaba?

> **Pendiente del equipo.** Escriban aquí, con sus palabras, qué esperaban encontrar y no encontraron. Algunas preguntas para orientarse (no las copien como respuesta):
> - ¿Esperaban ejemplos con datos o tableros, y no solo con código de aplicación?
> - ¿Esperaban una guía sobre cómo validar el significado de un dato (por ejemplo, cuándo un vacío es cero) y no solo su formato?
> - ¿Esperaban algo sobre equipos de estudiantes o proyectos pequeños sin revisores dedicados?

## Los tres cambios en nuestra forma de trabajar

| # | Qué cambiamos | Dónde lo ponemos | Por qué ahí |
|---|---|---|---|
| 1 | Cada push y pull request valida el CSV contra el contrato (tipos, códigos, columnas, variables derivadas) y corre las pruebas; si falla, el cambio queda en rojo y no se integra. | **Dentro del pipeline**: `.github/workflows/validar-datos.yml` | Son reglas sin excepciones: una columna numérica nunca puede llegar como texto. El asistente puede ignorar una instrucción; el pipeline no. |
| 2 | Las convenciones que requieren criterio van escritas para el asistente: supresión de grupos con n < 30, etiquetas dato / calculado / simulado, no usar edad ni género para elegir intervenciones, y los comandos de verificación. | **Fuera del pipeline**: `CLAUDE.md` en la raíz del repositorio | Tienen excepciones (por ejemplo, la vista restringida puede mostrar individuos seudonimizados), así que necesitan juicio, no un bloqueo automático. |
| 3 | Antes de aprobar un pull request que agrega o cambia una columna del tablero, un compañero revisa que tenga su renglón en `contrato-datos.md` y que el equipo haya decidido qué significa su vacío. | **Fuera del pipeline**: revisión humana del pull request | Decidir si un vacío es «sin dato», «cero» o «no aplica» depende del negocio; ni el asistente ni el pipeline pueden decidirlo. |
