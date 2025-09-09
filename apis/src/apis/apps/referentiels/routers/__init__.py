from apis.apps.referentiels.routers.code_programme import router as router_programme
from apis.apps.referentiels.routers.qpv import router as router_qpv

all_referentiel_routers = [
    router_programme,
    router_qpv,
]
