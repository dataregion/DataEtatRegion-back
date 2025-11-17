#!/usr/bin/env python3
"""
Test de charge Locust pour l'API Budget v3 avec assertions de performance
Usage: locust -f locust_budget_v3.py
"""

import requests
from locust import HttpUser, task, between, events
from tests_e2e.load_tests.thresholds import GLOBAL_PERFORMANCE_THRESHOLDS
from tests_e2e.load_tests.configuration import (
    api_base_url,
    client_id,
    client_secret,
    keycloak_realm,
    keycloak_url,
    password,
    username,
)
import sys


class BudgetV3LoadTest(HttpUser):
    wait_time = between(1, 3)

    def __init__(self, *args, **kwargs):
        self.host = api_base_url()
        super().__init__(*args, **kwargs)

    def on_start(self):
        """Initialisation : récupération du token d'authentification"""
        self.token = self._get_real_token()
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.api_v3_base = self._get_api_v3_base()

    def _get_api_v3_base(self):
        api_v3 = f"{self.host}/financial-data/api/v3"
        return api_v3

    def _get_real_token(self):
        """Récupère un token réel depuis Keycloak"""
        token_url = (
            f"{keycloak_url()}/realms/{keycloak_realm()}/protocol/openid-connect/token"
        )

        data = {
            "grant_type": "password",
            "client_id": client_id(),
            "username": username(),
            "password": password(),
        }
        if client_secret():
            data["client_secret"] = client_secret()

        response = requests.post(token_url, data=data)

        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            raise RuntimeError(
                f"Impossible de récupérer un token réel: {response.status_code}"
            )
    
    def _default_params(self):
        return {
            'force_no_cache': 'true'
        }

    @task(5)
    def get_lignes_default(self):
        """Test GET /lignes par défaut (tâche la plus fréquente)"""
        endpoint_name = "GET /lignes"

        params = self._default_params()

        with self.client.get(
            f"{self.api_v3_base}/lignes",
            params=params,
            headers=self.headers,
            name=endpoint_name,
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"Status: {response.status_code}")
            else:
                response.success()

    @task(5)
    def get_lignes_avec_beneficiaire(self):
        """Test GET /lignes par défaut (tâche la plus fréquente)"""
        endpoint_name = "GET /lignes?beneficiaires"

        params = self._default_params()
        params.update({"beneficiaire_code": "26350579400028,18310021300028"})

        with self.client.get(
            f"{self.api_v3_base}/lignes",
            params=params,
            headers=self.headers,
            name=endpoint_name,
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"Status: {response.status_code}")
            else:
                response.success()


@events.quitting.add_listener
def check_performance_on_quit(environment, **kwargs):
    """Analyse les statistiques finales et vérifie les seuils de performance"""
    stats = environment.stats
    performance_failures = []

    print("\n📊 ANALYSE DES PERFORMANCES:")
    print("=" * 80)
    print(
        f"{'Endpoint':<35} {'Requêtes':<10} {'Moy(ms)':<10} {'Min(ms)':<10} {'Max(ms)':<10} {'Status':<10}"
    )
    print("-" * 80)

    _items = stats.entries.items()
    if len(_items) == 0:
        raise RuntimeError("Aucune statistique collectée, le test a-t-il été exécuté ?")
    for name, stat in _items:
        assert type(name) is tuple
        name = name[0]

        if stat.num_requests == 0:
            continue

        avg_time = stat.avg_response_time
        min_time = stat.min_response_time
        max_time = stat.max_response_time
        num_requests = stat.num_requests

        # Vérifier les seuils pour cet endpoint
        thresholds = GLOBAL_PERFORMANCE_THRESHOLDS.get(name, {"avg": 0, "max": 0})
        avg_threshold = thresholds["avg"]
        max_threshold = thresholds["max"]

        # Déterminer le statut
        status = "✅ OK"
        if avg_time > avg_threshold:
            status = "❌ AVG"
            performance_failures.append(
                {
                    "endpoint": name,
                    "type": "avg",
                    "value": avg_time,
                    "threshold": avg_threshold,
                }
            )
        elif max_time > max_threshold:
            status = "⚠️ MAX"
            performance_failures.append(
                {
                    "endpoint": name,
                    "type": "max",
                    "value": max_time,
                    "threshold": max_threshold,
                }
            )

        print(
            f"{name:<35} {num_requests:<10} {avg_time:<10.0f} {min_time:<10.0f} {max_time:<10.0f} {status:<10}"
        )

    print("=" * 80)

    # Résumé final
    if performance_failures:
        print("\n❌ ÉCHEC DES TESTS DE PERFORMANCE:")
        print(f"   {len(performance_failures)} endpoints ne respectent pas les seuils")

        for failure in performance_failures:
            print(
                f"   - {failure['endpoint']}: {failure['type'].upper()} {failure['value']:.0f}ms > {failure['threshold']}ms"
            )

        print("\n💡 Seuils configurés dans GLOBAL_PERFORMANCE_THRESHOLDS")

        # Faire échouer le processus pour CI/CD
        environment.process_exit_code = 1
        sys.exit(1)
    else:
        total_requests = sum(stat.num_requests for stat in stats.entries.values())
        print("\n✅ TESTS DE PERFORMANCE RÉUSSIS:")
        print(f"   {len(stats.entries)} endpoints testés")
        print(f"   {total_requests} requêtes au total")
        print("   Tous les endpoints respectent les seuils de performance")
