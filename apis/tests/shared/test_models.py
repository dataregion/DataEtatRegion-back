import pytest
from http import HTTPStatus
from apis.shared.models import APIError, APISuccess, APIResponse


####
def _api_reponse_ctor(**kwargs):
    return APIResponse(**kwargs)


def _api_success_ctor(**kwargs):
    return APISuccess(**kwargs)


def _api_error_ctor(**kwargs):
    return APIError(**kwargs)


##


@pytest.mark.parametrize(
    "code_input, ctor, expected_code",
    [
        (HTTPStatus.ACCEPTED, _api_reponse_ctor, 202),
        (202, _api_reponse_ctor, 202),
        (HTTPStatus.BAD_REQUEST, _api_error_ctor, 400),
        (400, _api_error_ctor, 400),
        (HTTPStatus.BAD_GATEWAY, _api_success_ctor, 502),
        (502, _api_success_ctor, 502),
    ],
)
def test_api_response_code_are_int(code_input, ctor, expected_code):
    model = ctor(code=code_input)
    assert model.code == expected_code


def test_api_success_has_success_to_true():
    api_error = APISuccess(code=200)

    assert api_error.success is True


def test_api_error_has_success_to_false():
    api_error = APIError(code=400)

    assert api_error.success is False

def test_api_success_pagination():
    model = APISuccess(code = 200, current_page=0, has_next=True)

    assert model.pagination is not None
    assert model.pagination.current_page == 0
    
    with pytest.raises(ValueError):
        _ = APISuccess(code = 200, current_page=200)
    with pytest.raises(ValueError):
        _ = APISuccess(code = 200, has_next=False)
    
    #
    with pytest.raises(Exception):
        model.current_page=1
    with pytest.raises(Exception):
        model.has_next=False
    
    #
    serialized = model.model_dump()
    assert serialized['pagination'] == { "current_page": 0, "has_next": True }