#!/usr/bin/env python3
"""
Quick Seed Script - Genera datos simulados para Blinky API
Ejecuta solo el seeding, asume que la DB ya está inicializada
"""

import os
import sys
import subprocess

def run_command(command, description):
    """Ejecuta un comando y maneja errores"""
    print(f"\n{description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("[OK] Completado exitosamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Fallo: {e}")
        print(f"Detalles: {e.stderr}")
        return False

def main():
    print("=" * 50)
    print("   QUICK SEED - Datos Simulados Blinky API")
    print("=" * 50)

    # Cambiar al directorio raíz del proyecto
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)

    # Generar datos simulados
    seed_command = "python -m scripts.seed_demo_metrics --days 30 --users 20 --conversations-per-user 5 --messages-per-conversation 20 --seed 42"
    if not run_command(seed_command, "Generando datos simulados"):
        print("\n[ERROR] No se pudieron generar los datos simulados")
        sys.exit(1)

    print("\n" + "=" * 50)
    print("   [SUCCESS] DATOS SIMULADOS GENERADOS")
    print("=" * 50)
    print("\nResumen generado:")
    print("- 20 usuarios")
    print("- 5 conversaciones por usuario (100 total)")
    print("- 20 mensajes por conversacion (2000 mensajes)")
    print("- Periodo: 30 dias")
    print("- Incluye metricas de error y access_denied")
    print("\nEndpoints listos para probar:")
    print("- GET /api/metrics/dashboard")
    print("- GET /api/metrics/volume?hours=24")
    print("- GET /api/metrics/response-time?days=7")
    print("- GET /api/metrics/user-stats")
    print("\n[READY] ¡Todo listo!")

if __name__ == "__main__":
    main()