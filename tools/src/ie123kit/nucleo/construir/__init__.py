"""Construcción: candidatas por capas, entorno de capa, instalación, ROM y parche.

* ``candidata``: candidata (archive.fa + CRO) por capas y aportaciones sobre un B123 base.
* ``capas``: ``Capa(__file__)`` y ``ejecutar(main)``, en lugar del bootstrap copiado en work/.
* ``instalar``: instalación en el LayeredFS de Azahar con rehash fichero a fichero.
* ``rom``: reconstrucción local de la .3ds con 3dstool sobre una copia temporal del RomFS.
* ``parche``: generación del .xdelta, el único entregable que se distribuye.
* ``registro_azahar`` y ``limpieza``: cosecha de errores de runtime y limpieza de work/.
"""
