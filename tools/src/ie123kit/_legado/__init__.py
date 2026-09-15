"""Fachadas de compatibilidad; solo las importan los shims de tools/."""

CUARENTENA = frozenset({"ds_roster", "reinsert_var", "ssd_reinsert", "validate"})
EXCLUIDOS_DEL_REGISTRO = CUARENTENA | {"ds_official"}
BANDERA_LEGADO = "--legado-lo-se"
