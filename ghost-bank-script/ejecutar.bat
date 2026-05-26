@echo off
REM Script para ejecutar el procesador de PDFs

setlocal enabledelayedexpansion

echo.
echo ========================================
echo  PROCESADOR DE PDFs IDEMPOTENTE
echo ========================================
echo.

REM Verificar que ejecutar.py existe
if not exist "ejecutar.py" (
    echo ERROR: No se encuentra ejecutar.py
    pause
    exit /b 1
)

REM Si se pasa un argumento, usarlo como carpeta
if not "%~1"=="" (
    echo Carpeta a procesar: %~1
    python ejecutar.py "%~1"
) else (
    python ejecutar.py
)

echo.
echo ========================================
echo  PROCESO COMPLETADO
echo ========================================
echo.
echo CSV guardado en: resumen-de-extracción-CONSOLIDADO.csv
echo Reporte en: resumen-procesamiento-CONSOLIDADO.txt
echo.
pause
