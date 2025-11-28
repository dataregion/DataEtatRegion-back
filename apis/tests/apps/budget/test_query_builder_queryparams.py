"""Teste les proprietés de cache des query params pour les lignes financières."""

from pytest import fixture

from models.value_objects.colonne import Colonne
from services.budget.query_params import BudgetQueryParams


@fixture()
def default_query_params():
    inst = BudgetQueryParams.make_default()
    return inst


def test_default_query_params_is_total_cacheable():
    default_query_params = BudgetQueryParams.make_default()
    cache_key = default_query_params.get_total_cache_key()
    assert isinstance(default_query_params, BudgetQueryParams)
    assert hash(cache_key), "La clé de cache doit être hachable"


def test_two_different_query_params_gives_two_different_total_cache_keys():
    query_params_1 = BudgetQueryParams.make_default()
    query_params_2 = BudgetQueryParams.make_default()

    query_params_2.source_region = "52"  # La source region est un paramètre impliqué dans le calcul des totaux

    key1 = query_params_1.get_total_cache_key()
    key2 = query_params_2.get_total_cache_key()

    assert key1 != key2, "Les clefs ne doivent pas collisionner"
    assert hash(key1) != hash(key2), "Les clefs ne doivent pas collisionner"


def test_when_query_params_has_property_making_it_total_uncacheable():
    query_params = BudgetQueryParams.make_default()
    query_params.search = "toto"  # le paramètre search rend le paramètre non éligible au caching
    query_params.fields_search = "beneficiaire"

    total_cache_key = query_params.get_total_cache_key()
    assert total_cache_key is None


def test_when_property_doesnt_count_for_total_caching():
    query_params = BudgetQueryParams.make_default()
    key1 = query_params.get_total_cache_key()

    query_params.page = 2  # La page ne compte pas pour le calcul des totaux
    key2 = query_params.get_total_cache_key()

    assert id(key1) != id(key2), "Les clefs de cache doivent être des instances différentes"
    assert key1 == key2, "Les clefs de cache doivent être les mêmes"


def test_cache_with_grouping_and_grouped():
    colonne = Colonne(
        code="programme_code",
        label="Code Département du SIRET",
        concatenate="Code Département du SIRET",
        default=False,
        type=str,
    )
    query_params_1 = BudgetQueryParams.make_default()
    query_params_1.grouping = colonne.code
    query_params_1.grouped = "101"

    key1 = query_params_1.get_total_cache_key()

    # Vérifier que la clé est bien un frozenset et hashable
    assert isinstance(key1, frozenset), "La clé de cache doit être un frozenset"
    assert hash(key1), "La clé de cache doit être hachable"

    key_dict = dict(key1)
    # Vérifier que grouping contient bien notre colonne sous forme hashable
    assert key_dict["grouping"] == (colonne.code,), "Le grouping doit contenir le code de la colonne"
    assert key_dict["grouped"] == ("101",), "Le grouped doit contenir la valeur sous forme de tuple"
