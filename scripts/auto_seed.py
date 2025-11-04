#!/usr/bin/env python3
"""
Auto Seed Script - Genera datos simulados automáticamente para DP API
"""

import os
import sys
import subprocess

def run_command(command, description):
    """Ejecuta un comando y maneja errores"""
    print(f"\n{description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("✓ Completado exitosamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error: {e}")
        print(f"Salida de error: {e.stderr}")
        return False

def main():
    print("=" * 50)
    print("   AUTO SEED - Datos Simulados DP API")
    print("=" * 50)

    # Cambiar al directorio raíz del proyecto
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)

    # Inicializar base de datos
    if not run_command("python scripts/init_db.py", "Inicializando base de datos"):
        sys.exit(1)

    # Generar datos simulados
    seed_command = "python -m scripts.seed_demo_metrics --days 30 --users 20 --conversations-per-user 5 --messages-per-conversation 20 --seed 42"
    if not run_command(seed_command, "Generando datos simulados"):
        sys.exit(1)

    print("\n" + "=" * 50)
    print("   ✓ DATOS SIMULADOS GENERADOS EXITOSAMENTE")
    print("=" * 50)
    print("\nResumen:")
    print("- 20 usuarios")
    print("- 5 conversaciones por usuario (100 total)")
    print("- 20 mensajes por conversación (2000 mensajes)")
    print("- Período: 30 días")
    print("- Incluye métricas de error y access_denied")
    print("\nAhora puedes probar los endpoints:")
    print("- GET /api/metrics/dashboard")
    print("- GET /api/metrics/volume?hours=24")
    print("- GET /api/metrics/response-time?days=7")
    print("- GET /api/metrics/user-stats")
    print("\n¡Listo para usar!")

if __name__ == "__main__":
    main()