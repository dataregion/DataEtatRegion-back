"""Teste les query params, s'assure qu'ils soient compatibles avec le caching."""

import functools

import pytest
from services.shared.v3_query_params import V3QueryParams
from services.shared.source_query_params import SourcesQueryParams
from services.shared.financial_line_query_params import FinancialLineQueryParams


_global_cpt = 0


@functools.cache
def cache_a_query_param(query_param: V3QueryParams) -> int:
    global _global_cpt
    _global_cpt += 1
    return _global_cpt


def assert_similar_cache_keys(qp1: V3QueryParams, qp2: V3QueryParams):
    assert isinstance(qp1, V3QueryParams), "Le premier paramètre doit être une instance de V3QueryParams"
    assert isinstance(qp2, V3QueryParams), "Le deuxième paramètre doit être une instance de V3QueryParams"
    key1 = cache_a_query_param(qp1)
    key2 = cache_a_query_param(qp2)
    assert key1 == key2, "Les clés de cache doivent être identiques pour des query params similaires"


def assert_different_cache_keys(qp1: V3QueryParams, qp2: V3QueryParams):
    assert isinstance(qp1, V3QueryParams), "Le premier paramètre doit être une instance de V3QueryParams"
    assert isinstance(qp2, V3QueryParams), "Le deuxième paramètre doit être une instance de V3QueryParams"
    key1 = cache_a_query_param(qp1)
    key2 = cache_a_query_param(qp2)
    assert key1 != key2, "Les clés de cache doivent être différentes pour des query params différentes"


@pytest.mark.parametrize(
    "param1, param2",
    [
        (
            V3QueryParams(),
            V3QueryParams(),
        ),
        (
            V3QueryParams(colonnes="col1"),
            V3QueryParams(colonnes="col1"),
        ),
        (
            SourcesQueryParams(colonnes="col1"),
            SourcesQueryParams(colonnes="col1"),
        ),
        (
            FinancialLineQueryParams(colonnes="col1"),
            FinancialLineQueryParams(colonnes="col1"),
        ),
    ],
)
def test_cache_a_similar_query_param(param1, param2):
    assert_similar_cache_keys(param1, param2)


@pytest.mark.skip(
    reason="Ce n'est pas réellement nécessaire pour le fonctionnement de l'application, food4thought si besoin de faire évoluer les query params."
)
@pytest.mark.parametrize(
    "param1, param2",
    [
        (
            V3QueryParams(colonnes="col1"),
            V3QueryParams(colonnes="col1,"),
        ),
    ],
)
def test_cache_a_similar_query_param_edgecases(param1, param2):
    assert_similar_cache_keys(param1, param2)


@pytest.mark.parametrize(
    "param1, param2",
    [
        (
            V3QueryParams(),
            V3QueryParams(colonnes="col1,col2"),
        ),
        (
            V3QueryParams(colonnes="col1"),
            SourcesQueryParams(colonnes="col1,col2"),
        ),  # mêmes paramètres, mais classes différentes
        (
            SourcesQueryParams(colonnes="col1"),
            SourcesQueryParams(colonnes="col1,col2"),
        ),
        (
            FinancialLineQueryParams(colonnes="col1"),
            FinancialLineQueryParams(colonnes="col1,col2"),
        ),
    ],
)
def test_cache_a_different_query_param(param1, param2):
    assert_different_cache_keys(param1, param2)
