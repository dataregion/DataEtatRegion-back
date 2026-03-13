from unittest.mock import MagicMock, patch
from sqlalchemy import text
from datetime import datetime

import pytest
from sqlalchemy import select

from models import init as init_persistence_module

init_persistence_module()

from tests.flows.test_update_siret__utils import (  # noqa: E402
    _TEST_CATEGORIE_JURIDIQUE,
    _TEST_CODE_COMMUNE,
    _api_error,
    _make_mock_api_client,
    _make_mock_etablissement,
    _make_mock_etablissement_no_dependents,
)


from models.entities.refs.Siret import Siret  # noqa: E402
from .test_update_siret__utils import *  # noqa: E402, F403


# ──────────────────────────────────────────────
# Tests: update_one_siret (tâche Prefect)
# ──────────────────────────────────────────────


class TestUpdateOneSiret:
    @pytest.mark.anyio
    async def test_update_one_siret_with_non_existant_commune(
        self, session, sample_sirets, ref_dependants, prepare_update_siret_module_for_tests
    ):
        from batches.prefect.update_siret import _update_one_siret  # noqa: E402
        from models.entities.refs.Commune import Commune  # noqa: E402

        # given: un siret existant en base
        code = sample_sirets[0].code
        new_code_commune = "99999"  # Code commune qui n'existe pas en base

        # Vérifier que la commune n'existe pas
        commune_before = session.execute(select(Commune).where(Commune.code == new_code_commune)).scalar_one_or_none()
        assert commune_before is None

        # when: update_one_siret avec un code commune nouveau
        mock_client = _make_mock_api_client(with_dependents=True)
        mock_etablissement = _make_mock_etablissement(code_commune=new_code_commune)
        mock_client.donnees_etablissement.return_value = mock_etablissement

        result = await _update_one_siret(code, mock_client)

        # then: le siret doit être mis à jour
        assert result.success is True

        siret = session.execute(select(Siret).where(Siret.code == code)).scalar_one()
        assert siret.code_commune == new_code_commune

        # une ref_commune doit être initialisée avec le code
        commune_after = session.execute(select(Commune).where(Commune.code == new_code_commune)).scalar_one_or_none()
        assert commune_after is not None
        assert commune_after.code == new_code_commune

    @pytest.mark.anyio
    async def test_update_one_siret_success(
        self, session, sample_sirets, ref_dependants, prepare_update_siret_module_for_tests
    ):
        from batches.prefect.update_siret import _update_one_siret  # noqa: E402

        mock_client = _make_mock_api_client(with_dependents=True)
        code = sample_sirets[0].code

        result = await _update_one_siret(code, mock_client)

        assert result.success is True  # True = succès
        mock_client.donnees_etablissement.assert_called_once_with(code)

        # Vérifier que le SIRET a été mis à jour en base
        siret = session.execute(select(Siret).where(Siret.code == code)).scalar_one()
        assert siret.denomination == "MAIRIE DE RENNES"
        assert siret.code_commune == _TEST_CODE_COMMUNE
        assert siret.categorie_juridique == _TEST_CATEGORIE_JURIDIQUE

    @pytest.mark.anyio
    async def test_update_one_siret_api_error(self, session, sample_sirets, prepare_update_siret_module_for_tests):
        from batches.prefect.update_siret import _update_one_siret  # noqa: E402

        mock_client = _make_mock_api_client(etablissement_side_effect=_api_error())
        siret = sample_sirets[0].code

        result = await _update_one_siret(siret, mock_client)

        assert result.success is False
        assert result.siret == siret  # Retourne le code en cas d'erreur

    @pytest.mark.anyio
    async def test_update_one_siret_no_data_from_api(
        self, session, sample_sirets, prepare_update_siret_module_for_tests
    ):
        from batches.prefect.update_siret import _update_one_siret  # noqa: E402

        mock_client = MagicMock()
        mock_client.donnees_etablissement.return_value = None
        siret = sample_sirets[0].code

        result = await _update_one_siret(siret, mock_client)

        assert result.success is False  # True = succès

    @pytest.mark.anyio
    async def test_update_one_siret_no_data_still_updates_updated_at(
        self, session, sample_sirets, prepare_update_siret_module_for_tests
    ):
        from batches.prefect.update_siret import _update_one_siret  # noqa: E402

        code = sample_sirets[0].code
        siret_entity = session.execute(select(Siret).where(Siret.code == code)).scalar_one()
        original_updated_at = datetime(2000, 1, 1)
        siret_entity.updated_at = original_updated_at
        session.flush()

        mock_client = MagicMock()
        mock_client.donnees_etablissement.return_value = None

        result = await _update_one_siret(code, mock_client)

        session.refresh(siret_entity)

        assert result.success is False
        assert siret_entity.updated_at is not None
        assert siret_entity.updated_at > original_updated_at

    @pytest.mark.anyio
    async def test_update_one_siret_creates_new_if_not_exists(self, session, prepare_update_siret_module_for_tests):
        from batches.prefect.update_siret import _update_one_siret  # noqa: E402

        mock_client = _make_mock_api_client()  # sans FK
        code = "99999999999999"

        result = await _update_one_siret(code, mock_client)

        assert result.success is True
        siret = session.execute(select(Siret).where(Siret.code == code)).scalar_one_or_none()
        assert siret is not None
        assert siret.denomination == "MAIRIE DE RENNES"

    @pytest.mark.anyio
    async def test_update_one_siret_limit_hit(self, session, sample_sirets, prepare_update_siret_module_for_tests):
        from batches.prefect.update_siret import _update_one_siret  # noqa: E402
        from api_entreprise.exceptions import LimitHitError

        limit_error = LimitHitError.__new__(LimitHitError)
        limit_error.delay = 0  # Pas d'attente dans les tests

        # Premier appel -> LimitHitError, deuxième appel -> succès
        mock_client = MagicMock()
        mock_client.donnees_etablissement.side_effect = [limit_error, _make_mock_etablissement_no_dependents()]

        siret = sample_sirets[0].code

        result = await _update_one_siret(siret, mock_client)

        assert result.success is False


class TestQualification:
    """
    Tests de qualification pour s'assurer de certains comportements spécifiques de l'update siret
    """

    @pytest.mark.anyio
    async def test_flow_prioritizes_null_updated_at(self, session, prepare_update_siret_module_for_tests):
        """Vérifie que le flow met à jour en priorité les SIRETs avec updated_at=NULL."""
        from batches.prefect.update_siret import update_all_sirets  # noqa: E402

        # given: créer 4 SIRETs, dont 2 avec updated_at=NULL via SQL direct

        session.execute(
            text("""
            INSERT INTO ref_siret (code, updated_at)
            VALUES 
            ('11111111111111', NULL),
            ('22222222222222', NULL),
            ('33333333333333', '2020-01-01'),
            ('44444444444444', '2020-01-02')
        """)
        )
        session.commit()

        # Vérifier que les SIRETs ont bien été créés
        sirets_check = session.execute(select(Siret)).scalars().all()
        assert len(sirets_check) == 4
        assert sirets_check[0].updated_at is None
        assert sirets_check[1].updated_at is None

        mock_client = _make_mock_api_client()

        # act: lancer update_all_sirets avec max_sirets=3
        with patch("batches.prefect.update_siret._make_api_entreprise_client", return_value=mock_client):
            ctx = await update_all_sirets(max_sirets=3)

        # verify: tous les SIRETs ont été traités
        assert ctx.processed == 3
        assert ctx.success == 3
        assert ctx.errors == 0

        # Vérifier que tous les SIRETs ont un updated_at non-NULL
        sirets = session.execute(select(Siret)).scalars().all()
        for siret in sirets:
            assert siret.updated_at is not None

    @pytest.mark.anyio
    async def test_update_same_siret_twice_updates_update_date(
        self, session, sample_sirets, ref_dependants, prepare_update_siret_module_for_tests
    ):
        # given
        from batches.prefect.update_siret import _update_one_siret  # noqa: E402

        code = sample_sirets[0].code
        siret = session.execute(select(Siret).where(Siret.code == code)).scalar_one()
        arb_update_date = datetime(2000, 1, 1)
        siret.updated_at = arb_update_date
        original_udpate_at = siret.updated_at
        session.flush()

        mock_client = _make_mock_api_client(with_dependents=True)

        _ = await _update_one_siret(code, mock_client)

        session.refresh(siret)
        updated_at_maj1 = siret.updated_at

        # then
        _ = await _update_one_siret(code, mock_client)
        session.refresh(siret)
        updated_at_maj2 = siret.updated_at

        # assert
        assert original_udpate_at != updated_at_maj1 != updated_at_maj2, "Chaque update_at doit être différent"
        assert updated_at_maj2 > updated_at_maj1


# ──────────────────────────────────────────────
# Tests: update_all_sirets (flow Prefect)
# ──────────────────────────────────────────────


class TestUpdateAllSiretsFlow:
    @pytest.mark.anyio
    async def test_flow_stops_at_max_sirets(self, session, many_sirets, prepare_update_siret_module_for_tests):
        """Vérifie que le flow s'arrête après avoir traité max_sirets SIRETs."""
        from batches.prefect.update_siret import update_all_sirets  # noqa: E402

        mock_client = _make_mock_api_client()
        max_sirets = 3

        with patch("batches.prefect.update_siret._make_api_entreprise_client", return_value=mock_client):
            ctx = await update_all_sirets(max_sirets=max_sirets)

        assert ctx.processed == max_sirets
        assert ctx.total_in_db == 10
        assert mock_client.donnees_etablissement.call_count == max_sirets

    @pytest.mark.anyio
    async def test_flow_processes_all_when_limit_greater_than_total(
        self, session, sample_sirets, prepare_update_siret_module_for_tests
    ):
        """Vérifie que le flow traite tous les SIRETs quand max_sirets > total."""
        from batches.prefect.update_siret import update_all_sirets  # noqa: E402

        mock_client = _make_mock_api_client()

        with patch("batches.prefect.update_siret._make_api_entreprise_client", return_value=mock_client):
            ctx = await update_all_sirets(max_sirets=1000)

        assert ctx.processed == 3
        assert ctx.total_in_db == 3
        assert ctx.errors == 0

    @pytest.mark.anyio
    async def test_flow_counts_errors(self, session, sample_sirets, prepare_update_siret_module_for_tests):
        """Vérifie que les erreurs sont comptabilisées correctement."""
        from batches.prefect.update_siret import update_all_sirets  # noqa: E402

        mock_client = MagicMock()
        mock_client.donnees_etablissement.side_effect = [
            _make_mock_etablissement_no_dependents(),
            _api_error(),
            _api_error(),
        ]

        with patch("batches.prefect.update_siret._make_api_entreprise_client", return_value=mock_client):
            ctx = await update_all_sirets(max_sirets=1000)

        assert ctx.success == 1
        assert ctx.errors == 2
        assert ctx.processed == 3
        assert len(ctx.sirets_in_error) == 2

    @pytest.mark.anyio
    async def test_flow_raises_if_no_config(self, session, prepare_update_siret_module_for_tests):
        """Vérifie que le flow lève une erreur si la config API entreprise est absente."""
        from batches.prefect.update_siret import update_all_sirets  # noqa: E402

        with patch("batches.prefect.update_siret.get_config") as mock_config:
            mock_config.return_value.api_entreprise = None
            with pytest.raises(RuntimeError, match="api_entreprise"):
                await update_all_sirets(max_sirets=10)

    @pytest.mark.anyio
    async def test_flow_max_siret_with_errors(self, session, many_sirets, prepare_update_siret_module_for_tests):
        """Vérifie que la condition d'arrêt se base uniquement sur les SIRETs traités avec succès,
        pas sur les erreurs."""
        from batches.prefect.update_siret import update_all_sirets  # noqa: E402

        # Alternance succès / erreur
        side_effects = []
        for i in range(10):
            if i % 2 == 0:
                side_effects.append(_make_mock_etablissement_no_dependents())
            else:
                side_effects.append(_api_error())

        mock_client = MagicMock()
        mock_client.donnees_etablissement.side_effect = side_effects

        max_sirets = 3

        with patch("batches.prefect.update_siret._make_api_entreprise_client", return_value=mock_client):
            ctx = await update_all_sirets(max_sirets=max_sirets)

        # 3 succès atteints, le flow doit s'être arrêté
        assert ctx.processed == max_sirets
        assert ctx.success == 2
        assert ctx.errors == 1
