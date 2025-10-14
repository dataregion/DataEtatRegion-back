#!/usr/bin/env python3
"""
Script pour lancer les tests de performance Locust avec validation automatique
Usage: python run_performance_tests.py
"""

from pathlib import Path
import subprocess
import sys
import os
import argparse


def run_performance_test(users=10, spawn_rate=2, run_time="60s"):
    """Lance un test de performance en mode headless avec validation"""
    
    print("🚀 Lancement du test de performance...")
    print(f"   - Utilisateurs: {users}")
    print(f"   - Taux de montée: {spawn_rate}/s")
    print(f"   - Durée: {run_time}")
    print()
    
    # Commande Locust en mode headless
    filep = Path(os.path.dirname(__file__)) / "locust_budget_v3.py"
    cmd = [
        "locust",
        "-f", filep.as_posix(),
        "--headless",
        "-u", str(users),
        "-r", str(spawn_rate),
        "-t", run_time,
        "--html", "performance_report.html",
        "--csv", "performance_results"
    ]
    
    try:
        # Lancer Locust
        result = subprocess.run(cmd, capture_output=False)
        
        # Le code de sortie sera 1 si les performances ne sont pas assez bonnes
        if result.returncode == 0:
            print("\n✅ Tests de performance RÉUSSIS!")
            print("📊 Rapport HTML généré: performance_report.html")
            return True
        else:
            print("\n❌ Tests de performance ÉCHOUÉS!")
            print("📊 Rapport HTML généré: performance_report.html")
            print("💡 Vérifiez les seuils de performance dans locust_budget_v3.py")
            return False
            
    except FileNotFoundError:
        print("❌ Erreur: Locust n'est pas installé. Installez-le avec: pip install locust")
        return False
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Test de performance API Budget v3")
    parser.add_argument("--users", type=int, default=10, help="Nombre d'utilisateurs simultanés")
    parser.add_argument("--spawn-rate", type=int, default=2, help="Taux de montée (utilisateurs/sec)")
    parser.add_argument("--run-time", default="60s", help="Durée du test (ex: 60s, 2m)")
    
    args = parser.parse_args()
    
    success = run_performance_test(
        users=args.users,
        spawn_rate=args.spawn_rate,  
        run_time=args.run_time
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()