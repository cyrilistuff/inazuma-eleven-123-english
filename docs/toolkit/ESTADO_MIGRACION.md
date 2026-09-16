# Estado de la migración a ie123kit — PAUSADA (2026-09-16)

**Pausada por petición del usuario hasta que esté publicada la release 1.0**
(la que sustituye DeltaPatcher por IE-repack). No reanudar antes de eso.

## Hecho y cerrado en `main`

| Subfase | Issue | Commit |
|---|---|---|
| F1.0 línea base | #41 | `e87b084` |
| F1.1 esqueleto del paquete | #42 | `e66f54a` |
| F1.2 archivar retirados | #43 | `4d197ad`, `71c8146` |
| F1.3 motor a `nucleo` | #44 | `5c894f0`…`0af2abd` |
| F1.4 reparto por juego | #45 | `ba0e25f` |
| F1.5 CI y cierre de fase 1 | #46 | `cd5db31`, `a615aff`, `d4618bb` |
| F2.1 servicio y tipos | #47 | `79edbb6` |
| F2.2 primitivas y CLI mínima | #48 | `19805d7`, `c0fd108` |

## Pendiente

- **F2.3 (#49) a medias.** El trabajo sin terminar está en la rama
  `toolkit-f2.3-wip`, commit `bd7aeb2`: acciones por juego, cinemáticas y
  textos de IE1, reglas de IE2/IE3 y sus tests. **No pasó gate ni revisión**,
  así que no se fusiona en `main` sin superarlos.
- **F2.4 (#50)** orden `ie123`, scripts finos, retirada de shims de CLI.
- **F2.5 (#51)** preparación final para la GUI.
- Mejoras menores abiertas: #53, #54, #56, #57, #60, #61, #62, #63.
- Limpieza final (#55) después de F2.5.

## Cómo se reanuda

El workflow de agentes por subfase está en
`~/.claude/projects/C--Users-luish-Projects-inazuma-eleven-123-spanish/<sesión>/workflows/scripts/toolkit-migracion-f11-f25-wf_d8018915-118.js`.
Se reanuda con `Workflow({scriptPath, resumeFromRunId: 'wf_d8018915-118'})`, que
reutiliza lo ya completado. Si esa sesión ya no existe, se relanza el mismo
script sin `resumeFromRunId`: las subfases cerradas se detectan por `git log` en
la fase de plan.

Antes de reanudar, decidir qué hacer con `toolkit-f2.3-wip`: pasarle el gate y
fusionarla, o descartarla y dejar que la F2.3 se rehaga entera.

## Aviso: candidatas de referencia borradas (2026-09-16)

El usuario borró a mano `work/shared/candidatas/probe_ie1_v66` y `probe_ie1_v67` (y otras) para
liberar espacio. Son las candidatas golden de los gates (`tools/tests/compat/golden/candidatas.sha256`,
`test_bloqueo`, `requiere_rom`). **Antes de reanudar** hay que regenerarlas (v67 = v66 + capa
`work/ie1/capas/v67/titulo_logo`) o actualizar los golden a una candidata vigente.
