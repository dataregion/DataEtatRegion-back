from abc import ABC, abstractmethod
from http import HTTPStatus
from typing import Literal

from apis.shared.exceptions import BadRequestError
from fastapi import Query
from fastapi.params import Query as QueryCls


class CacheableTotalQuery(ABC):
    """Classe abstraite pour les requêtes qui peuvent être mises en cache"""

    @abstractmethod
    def _get_total_cache_dict(self) -> dict | None:
        """
        Retourne une clé de cache sous forme de dictionnaire ou None si la requête de totaux ne doit pas être mise en cache.

        Returns:
            dict | None: Dictionnaire représentant la clé de cache ou None
        """
        pass

    def get_total_cache_key(self) -> frozenset | None:
        cache_dict = self._get_total_cache_dict()
        if cache_dict is None:
            return None

        # Convertir les valeurs non-hashables en tuples
        hashable_items = []
        for key, value in cache_dict.items():
            if isinstance(value, list):
                if value is not None:
                    # Gérer les listes d'objets non-hashables
                    hashable_list = []
                    for item in value:
                        if hasattr(item, "code"):
                            hashable_list.append(item.code)
                        elif hasattr(item, "__dict__"):  # Objet standard avec attributs
                            hashable_list.append(frozenset(item.__dict__.items()))
                        else:
                            hashable_list.append(str(item))  # Fallback en string
                    hashable_items.append((key, tuple(hashable_list)))
                else:
                    hashable_items.append((key, None))
            else:
                hashable_items.append((key, value))

        return frozenset(hashable_items)


class V3QueryParams(CacheableTotalQuery):
    def __init__(
        self,
        colonnes: str | None = Query(None),
        page: int = Query(1, ge=1),
        page_size: int = Query(100, ge=1, le=1000),
        sort_by: str | None = Query(None),
        sort_order: Literal["asc", "desc"] | None = Query(None),
        search: str | None = Query(None),
        fields_search: str | None = Query(None),
    ):
        self.colonnes = self._split(colonnes)
        self.page = self._handle_default(page)
        self.page_size = self._handle_default(page_size)
        self.sort_by = self._handle_default(sort_by)
        self.sort_order = self._handle_default(sort_order)
        self.search = self._handle_default(search)
        self.fields_search = self._split(fields_search)

        if bool(self.sort_by) ^ bool(self.sort_order):
            raise BadRequestError(
                code=HTTPStatus.BAD_REQUEST,
                api_message="Les paramètres 'sort_by' et 'sort_order' doivent être fournis ensemble.",
            )
        if bool(self.search) ^ bool(self.fields_search):
            raise BadRequestError(
                code=HTTPStatus.BAD_REQUEST,
                api_message="Les paramètres 'search' et 'fields_search' doivent être fournis ensemble.",
            )

    def _split(self, val: str | None, separator: str = ",") -> list | None:
        val = self._handle_default(val)
        return val.split(separator) if val else None

    def _get_total_cache_dict(self) -> dict | None:
        return {
            "search": self.search,
            "fields_search": self.fields_search,
        }

    def _handle_default(self, val):
        if isinstance(val, QueryCls):
            return val.default
        return val
