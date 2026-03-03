"""Test unitaire pour le filtrage géographique de l'endpoint GET /lignes."""

import pytest
from fastapi.testclient import TestClient

from models.entities.refs.Region import Region
from models.entities.refs.Departement import Departement
from models.entities.refs.CentreCouts import CentreCouts
from models.entities.financial.query.FlattenFinancialLines import FlattenFinancialLines


@pytest.fixture(scope="session")
def setup_geographic_data(test_db):
    """
    Fixture qui setup les données géographiques et financières pour les tests.
    Insère dans la base :
    - 2 régions (Bretagne 53, Pays de la Loire 52)
    - 4 départements (22, 29 en Bretagne, 44, 85 en Pays de la Loire)
    - 4 centres de coûts avec départements
    - 4 lignes financières liées aux centres de coûts
    """
    from apis.database import get_session_main

    session = next(get_session_main())

    try:
        # Créer les régions
        region_bretagne = Region(
            code="53",
            label="Bretagne",
        )
        region_pdl = Region(
            code="52",
            label="Pays de la Loire",
        )
        session.add_all([region_bretagne, region_pdl])

        # Créer les départements
        dept_22 = Departement(
            code="22",
            label="Côtes-d'Armor",
            code_region="53",
        )
        dept_29 = Departement(
            code="29",
            label="Finistère",
            code_region="53",
        )
        dept_44 = Departement(
            code="44",
            label="Loire-Atlantique",
            code_region="52",
        )
        dept_72 = Departement(
            code="72",
            label="Sarthe",
            code_region="52",
        )
        dept_85 = Departement(
            code="85",
            label="Vendée",
            code_region="52",
        )
        session.add_all([dept_22, dept_29, dept_44, dept_72, dept_85])

        # Créer les centres de coûts
        cc_22 = CentreCouts(
            code="CC001",
            label="Centre de coûts 22",
            description="Centre en Côtes-d'Armor",
            code_departement="22",
        )
        cc_29 = CentreCouts(
            code="CC002",
            label="Centre de coûts 29",
            description="Centre en Finistère",
            code_departement="29",
        )
        cc_44 = CentreCouts(
            code="CC003",
            label="Centre de coûts 44",
            description="Centre en Loire-Atlantique",
            code_departement="44",
        )
        cc_72 = CentreCouts(
            code="CC072",
            label="Centre de coûts 72",
            description="Centre en Sarthe",
            code_departement="72",
        )
        cc_85 = CentreCouts(
            code="CC085",
            label="Centre de coûts 85",
            description="Centre en Vendée",
            code_departement="85",
        )
        session.add_all([cc_22, cc_29, cc_44, cc_72, cc_85])

        # Créer les lignes financières
        # Note: Dans les tests, flatten_financial_lines est une table, pas une vue matérialisée
        ligne_22 = FlattenFinancialLines()
        ligne_22.id = 1
        ligne_22.source = "FINANCIAL_DATA_AE"
        ligne_22.annee = 2024
        ligne_22.programme_code = "101"
        ligne_22.programme_label = "Programme Test"
        ligne_22.montant_ae = 100000.0
        ligne_22.montant_cp = 80000.0
        ligne_22.centreCouts_code = "CC022"
        ligne_22.centreCouts_label = "Centre de coûts 22"
        ligne_22.centreCouts_codeDepartement = "22"
        ligne_22.source_region = "53"
        ligne_22.data_source = "REGION"

        ligne_29 = FlattenFinancialLines()
        ligne_29.id = 2
        ligne_29.source = "FINANCIAL_DATA_AE"
        ligne_29.annee = 2024
        ligne_29.programme_code = "102"
        ligne_29.programme_label = "Programme Test 2"
        ligne_29.montant_ae = 150000.0
        ligne_29.montant_cp = 120000.0
        ligne_29.centreCouts_code = "CC029"
        ligne_29.centreCouts_label = "Centre de coûts 29"
        ligne_29.centreCouts_codeDepartement = "29"
        ligne_29.source_region = "53"
        ligne_29.data_source = "REGION"

        ligne_44 = FlattenFinancialLines()
        ligne_44.id = 3
        ligne_44.source = "FINANCIAL_DATA_AE"
        ligne_44.annee = 2024
        ligne_44.programme_code = "103"
        ligne_44.programme_label = "Programme Test 3"
        ligne_44.montant_ae = 200000.0
        ligne_44.montant_cp = 180000.0
        ligne_44.centreCouts_code = "CC044"
        ligne_44.centreCouts_label = "Centre de coûts 44"
        ligne_44.centreCouts_codeDepartement = "44"
        ligne_44.source_region = "53"
        ligne_44.data_source = "REGION"

        ligne_85 = FlattenFinancialLines()
        ligne_85.id = 4
        ligne_85.source = "FINANCIAL_DATA_AE"
        ligne_85.annee = 2024
        ligne_85.programme_code = "104"
        ligne_85.programme_label = "Programme Test 4"
        ligne_85.montant_ae = 250000.0
        ligne_85.montant_cp = 220000.0
        ligne_85.centreCouts_code = "CC085"
        ligne_85.centreCouts_label = "Centre de coûts 85"
        ligne_85.centreCouts_codeDepartement = "85"
        ligne_85.source_region = "53"
        ligne_85.data_source = "REGION"

        #  Centre de cout en 72 mais Beneficiaire dans le 22
        ligne_72 = FlattenFinancialLines()
        ligne_72.id = 5
        ligne_72.source = "FINANCIAL_DATA_AE"
        ligne_72.annee = 2024
        ligne_72.programme_code = "105"
        ligne_72.programme_label = "Programme Test 5"
        ligne_72.montant_ae = 90000.0
        ligne_72.montant_cp = 70000.0
        ligne_72.beneficiaire_code = "BENEF_22"
        ligne_72.beneficiaire_label = "Bénéficiaire dans 22"
        ligne_72.beneficiaire_commune_codeDepartement = "22"  # Code INSEE d'une commune dans le département 22
        ligne_72.centreCouts_code = "CC072"
        ligne_72.centreCouts_label = "Centre de coûts 72"
        ligne_72.centreCouts_codeDepartement = "72"
        ligne_72.source_region = "53"
        ligne_72.data_source = "REGION"

        session.add(ligne_72)

        session.add_all([ligne_22, ligne_29, ligne_44, ligne_85])
        session.commit()

        yield {
            "regions": [region_bretagne, region_pdl],
            "departements": [dept_22, dept_29, dept_44, dept_85, dept_72],
            "centres_couts": [cc_22, cc_29, cc_44, cc_85, cc_72],
            "lignes": [ligne_22, ligne_29, ligne_44, ligne_85, ligne_72],
        }

        # Cleanup - supprimer les données de test
        session.query(FlattenFinancialLines).delete(synchronize_session=False)
        session.query(CentreCouts).delete(synchronize_session=False)
        session.query(Departement).delete(synchronize_session=False)
        session.query(Region).delete(synchronize_session=False)
        session.commit()

    finally:
        # Fermer la session
        session.close()


def test_get_lignes_filter_by_department_on_centre_couts(client: TestClient, setup_geographic_data):
    """
    Test le filtrage des lignes financières par département.
    On filtre sur le département 85 et on vérifie qu'on ne récupère
    que les lignes dont le centre de coûts est dans ce département.
    """
    # Appel de l'API avec filtre département 85
    response = client.get(
        "/financial-data/api/v3/lignes",
        params={
            "niveau_geo": "DEPARTEMENT",
            "code_geo": "85",
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Vérifier que la réponse contient des lignes
    assert "data" in data
    assert "lignes" in data["data"]
    lignes = data["data"]["lignes"]

    # On doit avoir seulement 1 ligne (celle du centre de coûts en département 85)
    assert len(lignes) == 1
    assert lignes[0]["centreCouts_code"] == "CC085"


def test_get_lignes_filter_by_region_pdl_on_centre_couts(client: TestClient, setup_geographic_data):
    """
    Test le filtrage des lignes financières par région.
    On filtre sur la région 52 (Pays de la Loire) et on vérifie qu'on récupère
    toutes les lignes dont le centre de coûts est dans les départements de cette région.
    """
    # Appel de l'API avec filtre région 52 (Pays de la Loire)
    response = client.get(
        "/financial-data/api/v3/lignes",
        params={
            "niveau_geo": "REGION",
            "code_geo": "52",
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Vérifier que la réponse contient des lignes
    assert "data" in data
    assert "lignes" in data["data"]
    lignes = data["data"]["lignes"]

    # On doit avoir 3 lignes (celles des centres de coûts en départements 44, 85 et 72, qui sont en PDL)
    assert len(lignes) == 3
    codes_dept = {ligne["centreCouts_code"] for ligne in lignes}
    assert codes_dept == {"CC044", "CC085", "CC072"}


def test_get_lignes_filter_by_multiple_departments_on_centre_couts(client: TestClient, setup_geographic_data):
    """
    Test le filtrage des lignes financières par plusieurs départements.
    On filtre sur les départements 85 et 44.
    """
    # Appel de l'API avec filtres départements 85 et 44
    response = client.get(
        "/financial-data/api/v3/lignes",
        params={
            "niveau_geo": "DEPARTEMENT",
            "code_geo": "85,44",
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Vérifier que la réponse contient des lignes
    assert "data" in data
    assert "lignes" in data["data"]
    lignes = data["data"]["lignes"]

    # On doit avoir 2 lignes (départements 85 et 44)
    assert len(lignes) == 2
    codes_dept = {ligne["centreCouts_code"] for ligne in lignes}
    assert codes_dept == {"CC085", "CC044"}


def test_get_lignes_filter_on_centre_couts_and_beneficiaire(client: TestClient, setup_geographic_data):
    """
    Test le filtrage des lignes financières par centre de coûts et bénéficiaire.
    On filtre sur le departement 22
    """
    # Appel de l'API avec filtre département 22
    response = client.get(
        "/financial-data/api/v3/lignes",
        params={
            "niveau_geo": "DEPARTEMENT",
            "code_geo": "22",
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Vérifier que la réponse contient des lignes
    assert "data" in data
    assert "lignes" in data["data"]
    lignes = data["data"]["lignes"]

    # On doit avoir 2 lignes : une avec le centre de couts dans le 22 et une avec le bénéficiaire dans le 22 (centre couts dans le 72)
    assert len(lignes) == 2
    codes_dept = {ligne["centreCouts_code"] for ligne in lignes}
    assert codes_dept == {"CC022", "CC072"}
