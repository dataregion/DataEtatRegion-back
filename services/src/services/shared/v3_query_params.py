from abc import ABC, abstractmethod
from http import HTTPStatus
from typing import List, Literal, Optional

from models.exceptions import BadRequestError
from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator
from services.budget.colonnes import get_list_colonnes_tableau


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


class V3QueryParams(BaseModel, CacheableTotalQuery):
    model_config = ConfigDict(frozen=True)

    colonnes: Optional[str] = Field(default=None)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=100, ge=1, le=1000)
    sort_by: Optional[str] = Field(default=None)
    sort_order: Optional[Literal["asc", "desc"]] = Field(default=None)
    search: Optional[str] = Field(default=None)
    fields_search: Optional[str] = Field(default=None)

    @computed_field
    def colonnes_list(self) -> Optional[List[str]]:
        return self._split(self.colonnes)

    @computed_field
    def fields_search_list(self) -> Optional[List[str]]:
        return self._split(self.fields_search)

    @model_validator(mode="after")
    def post_init_v3(self):
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

        if self.sort_by is not None and self.sort_by not in [
            x.code for x in get_list_colonnes_tableau()
        ]:
            raise BadRequestError(
                code=HTTPStatus.BAD_REQUEST,
                api_message=f"La colonne demandée '{self.sort_by}' n'existe pas pour le tri.",
            )

        codes = self._split(self.fields_search) if self.fields_search else []
        if codes is not None and not all(
            field in [x.code for x in get_list_colonnes_tableau()] for field in codes
        ):
            raise BadRequestError(
                code=HTTPStatus.BAD_REQUEST,
                api_message=f"Les colonnes demandées '{self.fields_search}' n'existe pas pour la recherche.",
            )

        codes = self._split(self.colonnes) if self.colonnes else []
        for code in codes:
            found = [x for x in get_list_colonnes_tableau() if x.code == code]
            if len(found) == 0:
                raise BadRequestError(
                    code=HTTPStatus.BAD_REQUEST,
                    api_message=f"La colonne demandée '{code}' n'existe pas pour le tableau.",
                )
        return self

    @staticmethod
    def _split(val: Optional[str], separator: str = ",") -> Optional[List[str]]:
        if not val:
            return None
        return val.split(separator)

    def _get_total_cache_dict(self) -> dict | None:
        return {
            "search": self.search,
            "fields_search": self.fields_search_list,
        }
