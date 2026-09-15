# Tanda v38 — resto de pantallas de menú (issue #37)

Base: candidata v37 (`e1a2e936…a552376e`). Capa: `work/ie1/capas/v38/pantallas_nds` (apply + validate).
No se mueve ninguna coordenada de atlas; tipografía v20 bloqueada (PASS).

## Revisión por pantalla

| Pantalla · textura | Antes | Ahora | Origen |
|---|---|---|---|
| Capitán · sel_cap_mes_b03 | Pasión/Calma/Apoyo (Arial) | Pasión/Calma/**Seguir** pixel art | NDS `captainselect/CSDN_B01` |
| Capitán · sel_cap_window_b05 | Estrategia | **Táctica** | NDS `CSDN_W02` |
| Capitán · sel_cap_mes_b02 | やりなおす | Repetir | pintado |
| Enseñar técnica · teach_spm_mes_b02 | やりなおす | Repetir | pintado |
| Entrenamiento · tokkun_res_b_mes01 | けいけんち + rótulos Arial | rótulos cian + **EXP.** | NDS `msup_bg02` (como la ficha v37) |
| Escudo · sel_emb_mes_b02 | けってい/やめる | OK/Volver | pintado |
| Formación · form_mes_b03 | けってい/やめる | OK/Volver | pintado |
| Formación · form_nmes_b01 | 12 rótulos japoneses | Elegir, Tirar, Usar, Objetos, Técnicas, Botas, Tácticas, Accesorio, ¿Quién?, Guantes, Técnica, Formación | pintado |
| Archivador · binder_mes_b01 | índice あ..わ, 行, ページ | 1..10, (borrado), Pág. | pintado |
| Ojeador · scout_mes_panel02 | なまえ / 名前 | Nombre / Nombre | pintado |
| Teclado de nombre · font_kana01/hira01 | fila kana sobrante | borrada (bajo y=94) | limpieza |
| Miembros · point_plt_b01 (battle_member, _b) | píxeles blancos en la franja | franja naranja limpia | limpieza |

## Se quedan

- Rótulos rojos del entrenamiento Centella: ya en español y con estilo propio del 3DS.
- Resto de hojas en `work/ie1/capas/v38/estado` (bolsa, tienda, sistema, uniforme, inalámbrico…): ya en
  español, sin equivalente NDS con la misma forma.
- Residuos fuera de `a_menu` del informe v33 (escudos de `3ddemo_school`, pictogramas 風林火山 del
  mando de técnicas, `common`/`result`): quedan para otra tanda.

## Candidata

```
python work/ie1/capas/v38/pantallas_nds/apply.py
python work/ie1/capas/v38/pantallas_nds/validate.py
python tools/build_ui_revision.py --base work/shared/candidatas/probe_ie1_v37/archive.fa --ui work/ie1/capas/v38/pantallas_nds \
    --extra work/ie1/capas/v38/pantallas_nds/extra --cro work/shared/candidatas/probe_ie1_v37/romfs/cro/ina_main1.cro \
    --output work/shared/candidatas/probe_ie1_v38/archive.fa
python tools/verify_candidate.py --base work/shared/candidatas/probe_ie1_v37 --candidate work/shared/candidatas/probe_ie1_v38 \
    --layer work/ie1/capas/v38/pantallas_nds/extra
```

- `archive.fa`: `bac2944c534950c7a871fff328002610946b3a839b1ffcd9aa711e82c287b962`
- validate PASS (14 texturas en 10 .arc); verify: 10 reemplazos, 22 fuentes idénticas, 0 eventos,
  CRO idéntico, bloqueo PASS.
- 2026-09-15: instalada en Azahar; 70 SAD europeos intactos. Pendiente prueba en juego.
