@echo off
setlocal
title Comprobar ROM de Inazuma Eleven 1 2 3
if "%~1"=="" (
  echo Arrastra el archivo .3ds sobre Comprobar_ROM.bat.
  echo.
  pause
  exit /b 1
)
if not exist "%~1" (
  echo No se encuentra el archivo indicado:
  echo %~1
  echo.
  pause
  exit /b 1
)
for /f "skip=1 delims=" %%H in ('certutil -hashfile "%~1" SHA256') do if not defined HASH set "HASH=%%H"
set "HASH=%HASH: =%"
if not defined HASH (
  echo No se pudo calcular la huella del archivo.
  echo.
  pause
  exit /b 1
)
echo.
echo SHA-256: %HASH%
echo.
if /i "%HASH%"=="79bf42d3f22c6d9e7c7234919ee84007e346fbf421d3faf7ab2b688a0fc4cba2" (
  echo Compatible: ROM japonesa original. Sigue los DOS pasos de instrucciones.txt.
  goto end
)
if /i "%HASH%"=="73007ea1dc21e4a07a33f4038012ac66b03e644f89318b42a5d4997c79c6bbd5" (
  echo Compatible: traduccion v1. Aplica directamente el parche de actualizacion v1.1.
  goto end
)
if /i "%HASH%"=="aa5a9f6c5da4a2a98eb5dde97ceba51fa350cbff6f406893d5e08d515b9fd1e9" (
  echo Ya tienes la version v1.1.
  goto end
)
echo Archivo no compatible con estos parches. Revisa region, revision y cifrado.
:end
echo.
pause
