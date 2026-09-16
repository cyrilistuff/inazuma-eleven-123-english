"""Eventos: índice PackNum, registros SSD y preparación de scripts para reinsertar.

- ``packnum``: ``parse_index``/``entry_data`` y ``rebuild`` (reconstrucción del par
  .pkh/.pkb, parametrizada: sirve igual para eve y para mch).
- ``ssd``: ``TextRecord``, ``parse`` y ``replace`` de los registros de texto en línea.
- ``instrucciones``: ``EventPack`` (eve|mch) con ``events``/``instructions``/``find``
  y ``stage``, más ``comparar`` con las comprobaciones de identidad de
  ``build_ui_revision.rebuild_events``.
- ``alineado_ids``: emparejado de ids entre las versiones NDS y 3DS.
"""
