# Recuperación de codificación y fuentes de v13

El usuario aprueba el aspecto actual de v20 y ordena no volver a modificarlo.
La caja y la tipografía quedan bloqueadas en AGENTS.md y el generador comprueba
las fuentes, codificación y ajuste mediante `tools/dialogue_lock.py`.
Esta aprobación visual no certifica el recorrido completo de QA ni los capítulos.

La v19 falla visualmente: media caja vacía y letras superpuestas. No repetir la
afirmación de que recuperar solo las fuentes resuelve el problema.

La orden histórica conservada en `work/probe_ie1_v14_inputs/build-command.json`
construía v13 con `--fullwidth`. V14 y las candidatas generales posteriores
usaban ASCII. V19 restauró las cinco fuentes de v13, pero conservó ASCII: era una
restauración incompleta. No se ha demostrado que cambiara la geometría de la caja.

V20 conserva las cinco fuentes recuperadas y vuelve al transporte de ancho
completo con saltos por palabras. Las entradas de trabajo actuales siguen
cubiertas. Se prepararon 36 revisiones de longitud/codificación, sin truncamiento
automático y con comprobación del límite de cada registro. Se normalizan los
controles de página/línea para que el reflujo los reconozca.

El informe de esta comprobación se conserva dentro de la candidata actual
`work/probe_ie1_v21/archive.report.json`; el binario intermedio v20 se eliminó
tras instalar v21. El original de las traducciones anteriores sigue en
`work/probe_ie1_v14_inputs/reviewed.json`. No se conserva una ROM histórica v13
o v14.

Para el recorrido completo de regresión, usar arranque limpio, sin estados rápidos antiguos: Jack,
profesora, Andy, Nelly y puerta trasera. Validación estática no equivale a solución
visual. Instalar únicamente con Azahar cerrado. Tras verificar la instalación,
eliminar el binario anterior y conservar solo la candidata actual.
