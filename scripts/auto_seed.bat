@echo off
echo ========================================
echo    AUTO SEED - Datos Simulados DP API
echo ========================================
echo.

cd /d "%~dp0.."

echo Inicializando base de datos...
python scripts/init_db.py
if %errorlevel% neq 0 (
    echo ERROR: Fallo al inicializar la base de datos
    pause
    exit /b 1
)

echo.
echo Generando datos simulados...
python -m scripts.seed_demo_metrics --days 30 --users 20 --conversations-per-user 5 --messages-per-conversation 20 --seed 42
if %errorlevel% neq 0 (
    echo ERROR: Fallo al generar datos simulados
    pause
    exit /b 1
)

echo.
echo ========================================
echo    ✓ DATOS SIMULADOS GENERADOS EXITOSAMENTE
echo ========================================
echo.
echo Resumen:
echo - 20 usuarios
echo - 5 conversaciones por usuario (100 total)
echo - 20 mensajes por conversación (2000 mensajes)
echo - Período: 30 días
echo - Incluye métricas de error y access_denied
echo.
echo Ahora puedes probar los endpoints:
echo - GET /api/metrics/dashboard
echo - GET /api/metrics/volume?hours=24
echo - GET /api/metrics/response-time?days=7
echo - GET /api/metrics/user-stats
echo.
pause