from typing import TypedDict

class HasNext(TypedDict):
    hasNext: bool

    @staticmethod
    def jsonschema() -> dict:
        return {
          "type": "object",
          "properties": {
            "hasNext": {
              "type": "boolean"
            }
          },
          "required": ["hasNext"]
        } # type: ignore


class IncrementalPageOfBudgetLines(TypedDict):
    pagination: HasNext
    items: list