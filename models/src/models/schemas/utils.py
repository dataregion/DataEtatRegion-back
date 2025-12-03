import logging
from sqlalchemy.exc import InvalidRequestError


class MarshmallowSafeGetAttrMixin:
    """
    Mixin pour récupérer en toute sécurité les attributs des modèles SQLAlchemy dans les schémas Marshmallow.
    Utile lors de l'accès à des relations qui peuvent ne pas être chargées, évitant ainsi les erreurs.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mixin_enable_safe_getattr = False
        self._mixin_logger = logging.getLogger(__name__)

    def enable_safe_getattr(self):
        self._mixin_enable_safe_getattr = True
        return self

    def disable_safe_getattr(self):
        self._mixin_enable_safe_getattr = False
        return self

    def get_attribute(self, obj, attr, default):
        if self._mixin_enable_safe_getattr is False:
            val = super().get_attribute(obj, attr, default)
            return val

        try:
            val = super().get_attribute(obj, attr, default)
        except InvalidRequestError:  # XXX impossible de récupérer le valeur de l'attribut
            return None
        return val
