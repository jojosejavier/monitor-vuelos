@echo off
echo ========================================
echo  Monitor de Vuelos - Actualizando...
echo ========================================

echo.
echo [1/3] Consultando vuelos...
python monitor.py
if %errorlevel% neq 0 (
    echo ERROR al consultar vuelos. Abortando.
    pause
    exit /b 1
)

echo.
echo [2/3] Generando reporte...
python report.py
if %errorlevel% neq 0 (
    echo ERROR al generar reporte. Abortando.
    pause
    exit /b 1
)

echo.
echo [3/3] Publicando en GitHub Pages...
git add index.html
git commit -m "reporte: %date% %time%"
git push

echo.
echo ========================================
echo  Listo! Reporte publicado.
echo ========================================
pause
