import datetime
import shutil
from celery import current_task, subtask
from flask import current_app
from sqlalchemy import tuple_, delete
from app import celeryapp, db
from app.exceptions.exceptions import FinancialException
import sqlalchemy.exc
from app.models.financial.Ademe import Ademe
from app.models.financial.FinancialAe import COLUMN_MONTANT_NAME, FinancialAe
from app.models.financial.FinancialCp import FinancialCp
from app.models.financial.MontantFinancialAe import MontantFinancialAe
from app.models.refs.centre_couts import CentreCouts
from app.models.refs.code_programme import CodeProgramme
from app.models.refs.domaine_fonctionnel import DomaineFonctionnel
from app.models.refs.fournisseur_titulaire import FournisseurTitulaire
from app.models.refs.groupe_marchandise import GroupeMarchandise
from app.models.refs.localisation_interministerielle import LocalisationInterministerielle
from app.models.refs.referentiel_programmation import ReferentielProgrammation
from app.services.siret import check_siret
from app.tasks import limiter_queue

import pandas
import json
import requests
import tempfile

import os

from app.tasks.financial import logger, LineImportTechInfo
from app.tasks.financial.errors import _handle_exception_import


from app.utilities.observability import gauge_of_currently_executing, summary_of_time, SummaryOfTimePerfCounter

BATCH_SIZE = current_app.config.get("IMPORT_BATCH_SIZE", 10)


@limiter_queue(queue_name="line")
def _send_subtask_financial_ae(
    ae_batch: list[dict], source_region: str, annee: int, start_index: int, cp_lists: list[dict]
):
    # Envoyer le lot à la sous-tâche
    subtask("import_lines_financial_ae").delay(ae_batch, source_region, annee, start_index, cp_lists)


celery = celeryapp.celery


# TODO : deprecated
@celery.task(bind=True, name="import_file_ae_financial")
def import_file_ae_financial(self, fichier: str, source_region: str, annee: int):
    logger.debug(f"[IMPORT][FINANCIAL][AE] Start for region {source_region}, year {annee}, file {fichier}")
    timestamp = datetime.datetime.now().strftime("%Y%m%d")

    move_folder = current_app.config["UPLOAD_FOLDER"] + "/save/"
    try:
        data_chunk = pandas.read_csv(
            fichier,
            sep=",",
            header=0,
            names=FinancialAe.get_columns_files_ae(),
            dtype={"programme": str, "n_ej": str, "n_poste_ej": int, "fournisseur_titulaire": str, "siret": str},
            chunksize=1000,
        )
        series = pandas.Series({f"{FinancialAe.annee.key}": annee, f"{FinancialAe.source_region.key}": source_region})

        batch = []
        index = 0

        for chunk in data_chunk:
            for _, line in chunk.iterrows():
                ae_data = pandas.concat([line, series]).to_json()
                batch.append((ae_data, []))  # Ajouter une paire (AE data, CP list) au lot
                if len(batch) == BATCH_SIZE:
                    _send_subtask_financial_ae(batch, source_region, annee, index, [])  # Envoi du lot
                    batch = []  # Réinitialise le lot
                    index += BATCH_SIZE

        # Envoie les lignes restantes dans le lot
        if batch:
            _send_subtask_financial_ae(batch, source_region, annee, index, [])  # Envoi des lignes restantes

        move_folder = os.path.join(move_folder, timestamp)
        if not os.path.exists(move_folder):
            os.makedirs(move_folder)
        logger.debug(f"[IMPORT][FINANCIAL][AE] Save file {fichier} in {move_folder}")
        shutil.move(fichier, move_folder)
        logger.debug("[IMPORT][FINANCIAL][AE] End")
        return True
    except Exception as e:
        logger.exception(f"[IMPORT][FINANCIAL][AE] Error lors de l'import du fichier {fichier}")
        raise e


# TODO : deprecated
@celery.task(bind=True, name="import_file_cp_financial")
def import_file_cp_financial(self, fichier: str, source_region: str, annee: int):
    logger.debug(f"[IMPORT][FINANCIAL][CP] Start for region {source_region}, year {annee}, file {fichier}")
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    move_folder = current_app.config["UPLOAD_FOLDER"] + "/save/"

    try:
        current_taskid = current_task.request.id
        data_chunk = pandas.read_csv(
            fichier,
            sep=",",
            header=0,
            names=FinancialCp.get_columns_files_cp(),
            dtype={
                "programme": str,
                "n_ej": str,
                "n_poste_ej": str,
                "n_dp": str,
                "fournisseur_paye": str,
                "siret": str,
            },
            chunksize=1000,
        )

        cp_batch = []
        i = 0
        index = 0

        for chunk in data_chunk:
            for _, line in chunk.iterrows():
                i += 1
                tech_info = LineImportTechInfo(current_taskid, i)
                cp_batch.append({"data": line.to_json(), "task": tech_info})

                if len(cp_batch) == BATCH_SIZE:
                    _send_subtask_financial_cp(cp_batch, source_region, annee, index)
                    cp_batch = []  # Reset the batch
                    index += BATCH_SIZE

        # Send any remaining lines in the batch
        if cp_batch:
            _send_subtask_financial_cp(cp_batch, source_region, annee, index)

        move_folder = os.path.join(move_folder, timestamp)
        if not os.path.exists(move_folder):
            os.makedirs(move_folder)
        logger.info(f"[IMPORT][FINANCIAL][CP] Save file {fichier} in {move_folder}")
        shutil.move(fichier, move_folder)

        logger.info("[IMPORT][FINANCIAL][CP] End")
        return True
    except Exception as e:
        logger.exception(f"[IMPORT][FINANCIAL][CP] Error lors de l'import du fichier {fichier}")
        raise e


@celery.task(
    bind=True,
    name="import_lines_financial_ae",
    autoretry_for=(FinancialException,),
    retry_kwargs={"max_retries": 4, "countdown": 10},
)
@gauge_of_currently_executing()
@summary_of_time()
@_handle_exception_import("FINANCIAL_AE")
def import_lines_financial_ae(
    self, lines: list[str], source_region: str, annee: int, start_index: int, cp_list: list[dict] | None
):
    # Désérialisation de toutes les lignes en JSON
    line_data_list = [json.loads(line) for line in lines]

    perf_counter_retrieve_ae_instance = SummaryOfTimePerfCounter("import_line_financial_ae_retrieve_ae_instance")
    perf_counter_retrieve_ae_instance.start()
    try:
        # Préparation des données pour insertion et mise à jour en bulk
        new_aes = []
        montant_aes = []
        update_mappings = []

        for line_data in line_data_list:
            financial_ae_instance = (
                db.session.query(FinancialAe)
                .filter_by(n_ej=line_data[FinancialAe.n_ej.key], n_poste_ej=int(line_data[FinancialAe.n_poste_ej.key]))
                .one_or_none()
            )

            if financial_ae_instance:
                # Préparer les données pour la mise à jour
                update_mapping = financial_ae_instance.update_attribute(line_data)
                if update_mapping:
                    update_mappings.append(update_mapping)
            else:
                # Préparer une nouvelle instance pour l'insertion
                new_ae = FinancialAe(**line_data)
                new_aes.append(new_ae)

    except sqlalchemy.exc.OperationalError as o:
        logger.exception("[IMPORT][FINANCIAL][AE] Erreur sur le check des lignes")
        raise FinancialException(o) from o
    perf_counter_retrieve_ae_instance.observe()

    perf_counter_check_refs = SummaryOfTimePerfCounter("import_line_financial_ae_check_refs")
    perf_counter_check_refs.start()
    # Insertion des références en bulk
    _bulk_insert_references(new_aes)
    perf_counter_check_refs.observe()

    perf_insert_or_update_ae = SummaryOfTimePerfCounter("import_line_financial_ae_insert_or_update_ae")
    perf_insert_or_update_ae.start()

    # Insertion en bulk pour les nouvelles instances
    if new_aes:
        logger.debug(f"Insertion en bulk de {len(new_aes)} nouvelles instances de FinancialAe.")
        db.session.bulk_save_objects(new_aes)
        db.session.flush()  # Flush pour obtenir les IDs des nouvelles instances

        # Récupérer les nouvelles instances de FinancialAe pour s'assurer que les IDs sont bien générés
        ej_poste_ej_pairs = [(ae.n_ej, ae.n_poste_ej) for ae in new_aes]
        new_aes = (
            db.session.query(FinancialAe)
            .filter(tuple_(FinancialAe.n_ej, FinancialAe.n_poste_ej).in_(ej_poste_ej_pairs))
            .all()
        )

        # Maintenant que les IDs sont disponibles, créer les objets MontantFinancialAe
        for new_ae, line_data in zip(new_aes, line_data_list):
            montant_raw = line_data[COLUMN_MONTANT_NAME]
            if isinstance(montant_raw, str):
                montant = float(montant_raw.replace(",", "."))
            else:
                montant = float(montant_raw)
            montant_ae = MontantFinancialAe(montant=montant, annee=line_data[FinancialAe.annee.key])
            montant_ae.id_financial_ae = new_ae.id  # Associer l'ID de FinancialAe à MontantFinancialAe
            montant_aes.append(montant_ae)

    # Mise à jour en bulk pour les instances existantes
    if update_mappings:
        logger.debug(f"Mise à jour en bulk de {len(update_mappings)} instances existantes de FinancialAe.")
        db.session.bulk_update_mappings(FinancialAe, update_mappings)

    # Insertion des montants associés
    if montant_aes:
        logger.debug(f"Insertion de {len(montant_aes)} montants associés à FinancialAe.")
        db.session.bulk_save_objects(montant_aes)

    # Commit une seule fois après toutes les opérations
    db.session.commit()

    perf_insert_or_update_ae.observe()

    perf_trigger_cp = SummaryOfTimePerfCounter("import_line_financial_ae_trigger_cps")
    perf_trigger_cp.start()

    # Traitement des cp_list si nécessaire
    if cp_list is not None:
        cp_batch = []
        index = start_index  # Assurez-vous que l'index commence correctement

        # Itération sur la liste cp_list
        for struct in cp_list:
            cp_batch.append(struct)
            if len(cp_batch) == BATCH_SIZE:
                _send_subtask_financial_cp(cp_batch, source_region, annee, index)
                cp_batch = []
                index += BATCH_SIZE

        # Envoyer tout reste non envoyé
        if cp_batch:
            _send_subtask_financial_cp(cp_batch, source_region, annee, index)
    perf_trigger_cp.observe()


def _bulk_insert_references(new_aes):
    # Ensembles pour stocker les codes uniques à insérer
    code_programme_codes = set()
    centre_couts_codes = set()
    domaine_fonctionnel_codes = set()
    fournisseur_titulaire_codes = set()
    groupe_marchandise_codes = set()
    localisation_interministerielle_codes = set()
    referentiel_programmation_codes = set()

    try:
        for new_ae in new_aes:
            # Vérification pour CodeProgramme
            if not db.session.query(CodeProgramme).filter_by(code=str(new_ae.programme)).one_or_none():
                code_programme_codes.add(str(new_ae.programme))

            # Vérification pour CentreCouts
            if not db.session.query(CentreCouts).filter_by(code=str(new_ae.centre_couts)).one_or_none():
                centre_couts_codes.add(str(new_ae.centre_couts))

            # Vérification pour DomaineFonctionnel
            if not db.session.query(DomaineFonctionnel).filter_by(code=str(new_ae.domaine_fonctionnel)).one_or_none():
                domaine_fonctionnel_codes.add(str(new_ae.domaine_fonctionnel))

            # Vérification pour FournisseurTitulaire
            if hasattr(new_ae, "fournisseur_titulaire"):
                fournisseur_titulaire = new_ae.fournisseur_titulaire
            else:
                fournisseur_titulaire = new_ae.fournisseur_paye

            if not db.session.query(FournisseurTitulaire).filter_by(code=str(fournisseur_titulaire)).one_or_none():
                fournisseur_titulaire_codes.add(str(fournisseur_titulaire))

            # Vérification pour GroupeMarchandise
            if not db.session.query(GroupeMarchandise).filter_by(code=str(new_ae.groupe_marchandise)).one_or_none():
                groupe_marchandise_codes.add(str(new_ae.groupe_marchandise))

            # Vérification pour LocalisationInterministerielle
            if (
                not db.session.query(LocalisationInterministerielle)
                .filter_by(code=str(new_ae.localisation_interministerielle))
                .one_or_none()
            ):
                localisation_interministerielle_codes.add(str(new_ae.localisation_interministerielle))

            # Vérification pour ReferentielProgrammation
            if (
                not db.session.query(ReferentielProgrammation)
                .filter_by(code=str(new_ae.referentiel_programmation))
                .one_or_none()
            ):
                referentiel_programmation_codes.add(str(new_ae.referentiel_programmation))

            check_siret(new_ae.siret)

        # Conversion des ensembles en objets de modèle
        code_programme_instances = [CodeProgramme(code=code) for code in code_programme_codes]
        centre_couts_instances = [CentreCouts(code=code) for code in centre_couts_codes]
        domaine_fonctionnel_instances = [DomaineFonctionnel(code=code) for code in domaine_fonctionnel_codes]
        fournisseur_titulaire_instances = [FournisseurTitulaire(code=code) for code in fournisseur_titulaire_codes]
        groupe_marchandise_instances = [GroupeMarchandise(code=code) for code in groupe_marchandise_codes]
        localisation_interministerielle_instances = [
            LocalisationInterministerielle(code=code) for code in localisation_interministerielle_codes
        ]
        referentiel_programmation_instances = [
            ReferentielProgrammation(code=code) for code in referentiel_programmation_codes
        ]

        # Insertion en bulk pour les nouvelles instances
        if code_programme_instances:
            db.session.bulk_save_objects(code_programme_instances)
        if centre_couts_instances:
            db.session.bulk_save_objects(centre_couts_instances)
        if domaine_fonctionnel_instances:
            db.session.bulk_save_objects(domaine_fonctionnel_instances)
        if fournisseur_titulaire_instances:
            db.session.bulk_save_objects(fournisseur_titulaire_instances)
        if groupe_marchandise_instances:
            db.session.bulk_save_objects(groupe_marchandise_instances)
        if localisation_interministerielle_instances:
            db.session.bulk_save_objects(localisation_interministerielle_instances)
        if referentiel_programmation_instances:
            db.session.bulk_save_objects(referentiel_programmation_instances)

    except Exception as e:  # Attrape toutes les exceptions possibles
        logger.exception("[IMPORT][REF] Error lors de l'insertion en bulk des références.")
        raise e


@celery.task(bind=True, name="import_lines_financial_cp")
@summary_of_time()
@_handle_exception_import("FINANCIAL_CP")
def import_lines_financial_cp(self, cp_batch: list[dict], start_index: int, source_region: str, annee: int):
    perf_counter_create_cp_instance = SummaryOfTimePerfCounter("import_line_financial_cp_create_cp_instance")
    perf_counter_create_cp_instance.start()

    new_cps = []
    for i, cp in enumerate(cp_batch):
        line = json.loads(cp["data"])
        tech_info_list = cp["task"]
        tech_info = LineImportTechInfo(*tech_info_list)

        new_cp = FinancialCp(line, source_region=source_region, annee=annee)
        new_cp.file_import_taskid = tech_info.file_import_taskid
        new_cp.file_import_lineno = tech_info.lineno
        new_cp.id_ae = _get_ae_for_cp(new_cp.n_ej, new_cp.n_poste_ej)
        new_cps.append(new_cp)
    perf_counter_create_cp_instance.observe()

    perf_counter_check_refs = SummaryOfTimePerfCounter("import_line_financial_cp_check_refs")
    perf_counter_check_refs.start()
    _bulk_insert_references(new_cps)
    perf_counter_check_refs.observe()
    perf_counter_get_insert_cp = SummaryOfTimePerfCounter("import_line_financial_cp_insert_cp")
    perf_counter_get_insert_cp.start()

    db.session.bulk_save_objects(new_cps)
    db.session.commit()

    perf_counter_get_insert_cp.observe()


@celery.task(bind=True, name="import_file_ademe_from_website")
def import_file_ademe_from_website(self, url: str):
    response = requests.get(url, stream=True)
    response.raise_for_status()

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                temp_file.write(chunk)

        logger.info("Fichier téléchargé. Import...")
        _send_subtask_ademe_file(temp_file.name)


@celery.task(bind=True, name="import_file_ademe")
def import_file_ademe(self, fichier: str):
    logger.info(f"[IMPORT][ADEME] Start for file {fichier}")
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    move_folder = current_app.config["UPLOAD_FOLDER"] + "/save/"

    try:
        current_taskid = current_task.request.id
        data_ademe_chunk = pandas.read_csv(
            fichier,
            sep=",",
            header=0,
            dtype={"pourcentageSubvention": float, "idBeneficiaire": str, "idAttribuant": str, "notificationUE": str},
            chunksize=1000,
        )

        _delete_ademe()

        i = 0
        for chunk in data_ademe_chunk:
            for _, ademe_data in chunk.iterrows():
                i += 1
                tech_info = LineImportTechInfo(current_taskid, i)
                _send_subtask_ademe(ademe_data.to_json(), tech_info)

        move_folder = os.path.join(move_folder, timestamp)
        if not os.path.exists(move_folder):
            os.makedirs(move_folder)
        logger.info(f"[IMPORT][ADEME] Save file {fichier} in {move_folder}")

        shutil.move(fichier, move_folder)
        logger.info("[IMPORT][ADEME] End")

        return True
    except Exception as e:
        logger.exception(f"[IMPORT][ADEME] Error lors de l'import du fichier ademe: {fichier}")
        raise e


@celery.task(bind=True, name="import_line_ademe")
@_handle_exception_import("ADEME")
def import_line_ademe(self, line_ademe: str, tech_info_list: list):
    logger.debug(f"[IMPORT][ADEME][LINE] Traitement de la ligne ademe: {tech_info_list}")
    logger.debug(f"[IMPORT][ADEME][LINE] Contenu de la ligne ADEME : {line_ademe}")
    logger.debug(f"[IMPORT][ADEME][LINE] Contenu du tech info      : {tech_info_list}")

    tech_info = LineImportTechInfo(*tech_info_list)

    line = json.loads(line_ademe)
    new_ademe = Ademe.from_datagouv_csv_line(line)
    new_ademe.file_import_taskid = tech_info.file_import_taskid
    new_ademe.file_import_lineno = tech_info.lineno

    logger.info(
        f"[IMPORT][ADEME] Tentative ligne Ademe reference decision {new_ademe.reference_decision}, beneficiaire {new_ademe.siret_beneficiaire}"
    )

    # SIRET Attribuant
    check_siret(new_ademe.siret_attribuant)
    # SIRET beneficiaire
    check_siret(new_ademe.siret_beneficiaire)

    db.session.add(new_ademe)
    logger.info("[IMPORT][FINANCIAL] Ajout ligne financière")
    db.session.commit()

    logger.debug(f"[IMPORT][ADEME][LINE] Traitement de la ligne ademe: {tech_info_list}")


@limiter_queue(queue_name="file")
def _send_subtask_ademe_file(filepath: str):
    subtask("import_file_ademe").delay(filepath)


@limiter_queue(queue_name="line")
def _send_subtask_ademe(data_ademe: str, tech_info: LineImportTechInfo):
    subtask("import_line_ademe").delay(data_ademe, tech_info)


@limiter_queue(queue_name="line")
def _send_subtask_financial_cp(cp_batch: list[dict], source_region: str, annee: int, start_index: int):
    # Envoyer le lot complet à la sous-tâche
    subtask("import_lines_financial_cp").delay(cp_batch, start_index, source_region, annee)


def _get_ae_for_cp(n_ej: str, n_poste_ej: int) -> int | None:
    """
    Récupère le bon AE pour le lié au CP
    :param n_ej : le numero d'ej
    :parman n_poste_ej : le poste ej
    :return:
    """
    if n_ej is None or n_poste_ej is None:
        return None

    financial_ae = FinancialAe.query.filter_by(n_ej=str(n_ej), n_poste_ej=int(n_poste_ej)).one_or_none()
    return financial_ae.id if financial_ae is not None else None


def _delete_ademe():
    """
    Supprime toutes les données ADEME
    :return:
    """
    stmt = delete(Ademe)
    db.session.execute(stmt)
    db.session.commit()
