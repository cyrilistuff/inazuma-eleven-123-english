# QA estática del partido de la Royal en v21

Esta candidata quedó supersedida por v23. Sus 143 registros se conservan y se
reinsertan en `work/shared/candidatas/probe_ie1_v23/`; el informe vigente de la tanda completa es
[QA_PACHANGAS_MCH_V23.md](QA_PACHANGAS_MCH_V23.md).

La captura del usuario corresponde al paquete `inazuma1/data_iz/script/mch.pkb`,
evento `94001500`, registro visible 24. Ese registro no pertenece a `eve.pkb`,
por eso la traducción general anterior no lo alcanzaba.

- Registros visibles traducidos: 143 de 143.
- Japonés visible restante en ese evento: 0.
- Registro de la captura: `¡Vamos, chicos! ¡Derrotemos a la Royal Academy!`.
- Hash del registro japonés original: `6befe68512dbf1c4707299fc405d8c08556393287a0f2da58233beba6e714891`.
- Los otros 248 eventos de `mch` se conservan iguales tras descomprimirlos.
- Bytecode, índices SSD, fuentes aprobadas y caja de diálogo no se modifican.
- Candidata instalada: SHA-256 `45377d4e6a4987301d8770e454ce883124806ffc9b8674d8385762a22ff4f566`.

La prueba jugable aún no está cerrada. Hay que reiniciar Azahar para cargar la
candidata y evitar estados rápidos creados con otra build; el usuario controla
el recorrido y el agente observa las capturas y el registro sin enviar entradas.
