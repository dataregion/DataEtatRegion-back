# Description
Les tests d'intégration sont lancé sur un environnement d'intégration.
Le but est de tester des API global de data-transform.


# Pré-requis:
Pour lancer les tests E2E il faut un stack backend complet :
- API
- BDD
- Keycloak
- Grist etc....  



Les tests se lancent en locale via la commande
```
pytest -v .
```


Il est possible de tester sur d'autres environnement en spécifiant les URI, config en ligne de commande ou via variable d'environnement.

Voici les variables disponibles :

| Variable  | option ligne de commande | option ligne de commande | valeur défaut en locale |
| :--------------- |:---------------:| :-----:| :------:|
| Url API data-transform  |   --api-url  | API_BASE_URL  | http://localhost:5000 |



## Exemple
Pour lancer les tests : 
```
pytest -v . --api-url="https://<URL_API>"
```