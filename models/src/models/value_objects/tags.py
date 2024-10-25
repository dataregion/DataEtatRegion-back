# region app model


from dataclasses import dataclass


def _sanitize_tag_prettyname(pretty_name: str):
    if ":" not in pretty_name:
        return pretty_name + ":"
    return pretty_name


@dataclass
class TagVO:
    """Représente un tag (i.e: un type et une valeur). C'est un value object"""

    type: str
    value: str | None

    @property
    def fullname(self):
        """
        fullname d'un tag correctement formatté pour requête avec la bdd
        voir :meth:`app.models.tags.Tags.fullname`
        """
        type = self.type or ""
        value = self.value or ""
        pretty = f"{type}:{value}"
        return pretty

    @staticmethod
    def from_prettyname(pretty: str):
        """
        Parse un nom de tag
        warning: pretty ne devient pas forcément le fullname du tag
        """
        fullname = _sanitize_tag_prettyname(pretty)
        split = fullname.split(":")
        type = split[0] or None
        value = split[1] or None

        if type is None:
            raise ValueError("Error during parsing tag prettyname. Type should not be empty")

        return TagVO.from_typevalue(type, value)

    @staticmethod
    def from_typevalue(type: str, value: str | None = None):
        return TagVO(type, value)

    @staticmethod
    def sanitize_str(pretty: str):
        """
        Corrige les prettyname des tags pour respecter
        la convention plus stricte de représentation des noms de tags.
        """
        tag = TagVO.from_prettyname(pretty)
        return tag.fullname