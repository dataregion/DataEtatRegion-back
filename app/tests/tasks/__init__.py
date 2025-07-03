from datetime import datetime

from models.entities.financial.Ademe import Ademe
from models.entities.financial.FinancialAe import FinancialAe
from models.entities.financial.FinancialCp import FinancialCp
from models.entities.refs import Siret


def build_siret(update_date: datetime):
    siret = Siret(**{"code": "90933627300000", "denomination": "TEST"})
    siret.updated_at = update_date
    return siret


def build_ademe(update_date: datetime):
    siret = build_siret(update_date)
    ademe = Ademe.from_datagouv_csv_line(
        {
            "objet": "objet",
            "dateConvention": "2025-04-02",
            "montant": "100.0",
            # proprietés osef
            "notificationUE": "",
            "referenceDecision": "",
            "nature": "",
            "conditionsVersement": "",
            "datesPeriodeVersement": "",
            "pourcentageSubvention": "2",
            "idAttribuant": siret.code,
            "idBeneficiaire": siret.code,
        }
    )
    ademe.updated_at = update_date
    return ademe


def build_financial_ae(update_date: datetime):
    f = FinancialAe(
        annee=2020,
        n_ej="1",
        n_poste_ej=1,
        programme="380",
        domaine_fonctionnel="0380-01-01",
        centre_couts="BG00\\/DREETS0035",
        referentiel_programmation="BG00\\/010300000108",
        fournisseur_titulaire="1001465507",
        siret=build_siret(update_date).code,
        localisation_interministerielle="N35",
        groupe_marchandise="groupe",
        date_modification_ej=datetime.now(),
        compte_budgetaire="co",
        data_source="REGION",
    )
    f.updated_at = update_date
    return f


def build_financial_cp(update_date: datetime):
    cp = FinancialCp(
        line_chorus={
            "annee": 2020,
            "n_ej": "1",
            "n_poste_ej": 1,
            "n_dp": "numero dp",
            "programme": "380",
            "domaine_fonctionnel": "0380-01-01",
            "centre_couts": "BG00\\/DREETS0035",
            "referentiel_programmation": "BG00\\/010300000108",
            "fournisseur_titulaire": 1001465507,
            "localisation_interministerielle": "N35",
            "fournisseur_paye": "1000373509",
            "groupe_marchandise": "groupe",
            "compte_budgetaire": "co",
            "siret": build_siret(update_date).code,
            "data_source": "REGION",
        },
        annee=2021,
        source_region="53",
    )
    cp.updated_at = update_date
    return cp
