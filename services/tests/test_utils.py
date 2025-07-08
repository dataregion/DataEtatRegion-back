import pytest
from services.utils import convert_exception, wrap_all_ex_to


@pytest.mark.parametrize(
    "raised, expected",
    [
        (
            Exception,
            Exception,
        ),
        (
            Exception,
            RuntimeError,
        ),
    ],
)
def test_convert_exception(raised, expected):
    def _fun():
        raise raised()

    decorated_fn = convert_exception(raised, expected)(_fun)

    with pytest.raises(expected) as e:
        decorated_fn()
    exc = e.value
    assert isinstance(exc, expected)
    if expected == raised:
        assert exc.__cause__ is None
    else:
        assert isinstance(exc.__cause__, raised)


def test_wrap_all_to_ex():
    assert returning_a_value() is True, "It should return true"

    with pytest.raises(CustomEx) as excinfo:
        raising_value_error()
    assert isinstance(excinfo.value.__cause__, ValueError)

    with pytest.raises(CustomEx) as excinfo:
        raising_custom_ex()
    assert excinfo.value.__cause__ is None, (
        "Le décorateur ne doit pas wrapper "
        "l'exception en paramètre si elle est soulevée dans le code client"
    )

    with pytest.raises(Exception) as excinfo:
        wrap_all_ex_to(CustomEx())  # XXX: on accepte seulement une classe


class CustomEx(Exception):
    pass


@wrap_all_ex_to(CustomEx)
def raising_value_error():
    raise ValueError("oops")


@wrap_all_ex_to(CustomEx)
def raising_custom_ex():
    raise CustomEx()


@wrap_all_ex_to(CustomEx)
def returning_a_value():
    return True
