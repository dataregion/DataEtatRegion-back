from prefect import serve
from batches.prefect.exporte_une_recherche import exporte_une_recherche
from batches.prefect.update_link_siret_qpv import update_link_siret_qpv_from_url


def main():
    export_recherche_deploiement = exporte_une_recherche.to_deployment(name="exporte_une_recherche")
    update_link_siret_qpv_from_url_deploiement = update_link_siret_qpv_from_url.to_deployment(name="update_link_siret_qpv_from_url")
    serve(
        export_recherche_deploiement,  # type: ignore
        update_link_siret_qpv_from_url_deploiement,  # type: ignore
    )


if __name__ == "__main__":
    main()
