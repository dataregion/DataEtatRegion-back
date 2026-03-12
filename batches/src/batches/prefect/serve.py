from prefect import serve
from batches.prefect.sync_referentiel_grist import sync_referentiel_grist_flow
from batches.prefect.exporte_une_recherche import exporte_une_recherche
from batches.prefect.import_file_qpv_lieu_action import import_file_qpv_lieu_action
from batches.prefect.share_filter_user import share_filter_user
from batches.prefect.update_link_siret_qpv import update_link_siret_qpv_from_url
from batches.prefect.update_siret import update_all_sirets


def main():
    export_recherche_deploiement = exporte_une_recherche.to_deployment(name="exporte_une_recherche")
    import_file_qpv_lieu_action_deploiement = import_file_qpv_lieu_action.to_deployment(
        name="import_file_qpv_lieu_action"
    )
    share_filter_user_deploiement = share_filter_user.to_deployment(name="share_filter_user")
    update_link_siret_qpv_from_url_deploiement = update_link_siret_qpv_from_url.to_deployment(
        name="update_link_siret_qpv_from_url",
        cron="0 0 ? * 6#2",  # Tous les deuxièmes samedi du mois
    )
    sync_referentiel_grist_deploiement = sync_referentiel_grist_flow.to_deployment(
        name="sync_referentiel_grist",
    )
    update_all_sirets_deploiement = update_all_sirets.to_deployment(
        name="update_all_sirets",
        cron="0 2 * * *",  # Tous les jours à 2h du matin
    )
    serve(
        export_recherche_deploiement,  # type: ignore
        import_file_qpv_lieu_action_deploiement,  # type: ignore
        share_filter_user_deploiement,  # type: ignore
        update_link_siret_qpv_from_url_deploiement,  # type: ignore
        sync_referentiel_grist_deploiement,  # type: ignore
        update_all_sirets_deploiement,  # type: ignore
    )


if __name__ == "__main__":
    main()
