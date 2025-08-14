from typing import Any, Literal

from pydantic import BaseModel

class _StubModel(BaseModel):
    data: Any

def _assert_can_jsonize(data, mode: Literal['json', 'python'] = 'python'):
    """Test if data can be jsonized"""
    response = _StubModel(data=data)
    dumped = response.model_dump(mode=mode)
    assert dumped is not None
    return dumped