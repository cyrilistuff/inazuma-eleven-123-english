# Distribución con DeltaPatcher

El proyecto distribuye únicamente un parche diferencial. La ROM traducida se
genera en el ordenador del usuario al aplicar el parche sobre su propia copia
legal y descifrada del cartucho. No se incluye ni se sube ninguna ROM.

## Release v1.1 (build IE1 v35)

La ROM base exacta dejó de estar disponible localmente después de preparar v1.
Para no publicar un xdelta incompatible, v1.1 se distribuye como actualización
comprobada sobre la v1:

- ROM v1 de entrada: SHA-256
  `73007ea1dc21e4a07a33f4038012ac66b03e644f89318b42a5d4997c79c6bbd5`.
- Parche: `inazuma123-es-v1.1-update.xdelta`, SHA-256
  `dbfb10c901a326c630d2e52eb19ed81921211ff16793a27db00cf3d8411ad041`.
- ROM v1.1 resultante, solo local: SHA-256
  `aa5a9f6c5da4a2a98eb5dde97ceba51fa350cbff6f406893d5e08d515b9fd1e9`.
- La reaplicación del parche reprodujo la candidata v35 byte a byte.

El ZIP portable incluye también el parche v1. Quien parte de la ROM japonesa
original aplica primero v1 y después la actualización v1.1; quien ya tiene v1
solo necesita el segundo paso. `release/instrucciones-v1.1.txt` documenta ambas
rutas y las huellas de entrada y salida.

## Release v1 (build IE1 v33) y publicación con Actions

- Parche: `patch/inazuma123-es-v1.xdelta`, generado en local con
  `work/v33/_final/build_rom.py` (RomFS con `archive.fa` y `ina_main1.cro` de la
  candidata v33, ExeFS original) y `xdelta3 -e -9 -B 2147483648`, y comprobado
  reaplicándolo sobre la ROM base (el resultado coincide byte a byte con la ROM
  compilada). Parche de 22.116.160 bytes, SHA-256
  `19fb1f417ded64894c7302f4cecab4bb1d93e193a6a037bcf60dac3aa7266b05`
  (`release/inazuma123-es-v1.xdelta.sha256`). ROM resultante (solo local, no se
  publica): `73007ea1dc21e4a07a33f4038012ac66b03e644f89318b42a5d4997c79c6bbd5`.
- El workflow `.github/workflows/release.yml` (lanzamiento manual) toma el parche
  (de `patch/` o de un borrador de la release), comprueba su hash, descarga
  DeltaPatcher oficial de `marco-calautti/DeltaPatcher` con su licencia GPL-2.0,
  añade `release/instrucciones.txt`, `release/TERCEROS.txt`, el lanzador y
  `SHA256SUMS.txt`, rechaza cualquier ROM o archivo extraído y publica la release
  con `release/notas-<tag>.md`.

```text
gh workflow run release.yml -f tag=v1 -f patch=inazuma123-es-v1.xdelta
```

## Paquete anterior (v27)

- Parche: [`patch/inazuma123-es-v27.xdelta`](../patch/inazuma123-es-v27.xdelta)
- SHA-256 del parche: `40d81657b9612b4bf232d92e1ae42fc35ddc03f2bbceeb1e94d67187c0e54d47`
- ROM base: *Inazuma Eleven 1·2·3!! Endō Mamoru Densetsu*, 3DS japonesa,
  descifrada (`CTR-P-AETJ`)
- SHA-256 de la ROM base usada para generar el parche:
  `79bf42d3f22c6d9e7c7234919ee84007e346fbf421d3faf7ab2b688a0fc4cba2`

El hash de la ROM base permite detectar un volcado de otra revisión o una ROM
encriptada antes de aplicar el parche. No es necesario publicar la ROM ni el
hash de la ROM traducida.

## Paquete portable preparado

La carpeta de trabajo contiene `work/release_inazuma123_es_v27_deltapatcher.zip`.
Incluye `instrucciones.txt`, `Lanzar_DeltaPatcher.bat`, el `DeltaPatcher.exe`
portable 3.1.6, el `.xdelta`, los checksums y el aviso de terceros. Está fuera
del control de versiones porque el ejecutable es una herramienta de terceros;
el paquete no contiene la ROM.

## Aplicación con DeltaPatcher

1. Descarga DeltaPatcher desde su distribución oficial y ábrelo.
2. En **Original file**, selecciona tu ROM `.3ds` legal y descifrada.
3. En **XDelta patch**, selecciona `inazuma123-es-v27.xdelta`.
4. En **Patched file**, elige un nombre nuevo, por ejemplo
   `inazuma123_es_v27.3ds`. Conserva intacta la ROM original.
5. Pulsa **Apply patch** y espera a que termine.
6. Abre el archivo generado en Azahar o Lime3DS.

La operación de DeltaPatcher equivale a fusionar localmente la ROM original con
el parche. El archivo resultante solo debe permanecer en el equipo del usuario;
no forma parte del repositorio ni del paquete distribuible.

## Alternativa por línea de comandos

Con `xdelta3` se puede hacer la misma operación:

```text
xdelta3 -d -f -s "tu_rom_original.3ds" \
  "inazuma123-es-v27.xdelta" "inazuma123_es_v27.3ds"
```

El parche está construido contra la ROM descifrada exacta indicada arriba. No
uses una CIA, una ROM encriptada, otra región o una revisión distinta.

## Qué se publica

La distribución de una versión contiene el `.xdelta`, su checksum y estas
instrucciones. No contiene `.3ds`, `.cia`, RomFS, ExeFS, `archive.fa`, fuentes,
gráficos ni otros archivos extraídos del juego.
