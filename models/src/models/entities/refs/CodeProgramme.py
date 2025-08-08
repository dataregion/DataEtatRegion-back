from models import _PersistenceBaseModelInstance
from models.entities.common.Audit import _Audit
from models.entities.common.SyncedWithGrist import _SyncedWithGrist
from models.entities.refs.Theme import Theme
from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relationship, Mapped


class CodeProgramme(_Audit, _SyncedWithGrist, _PersistenceBaseModelInstance()):
    __tablename__ = "ref_code_programme"
    id = Column(Integer, primary_key=True)
    code: Column[str] = Column(String, unique=True, nullable=False)
    # FK
    code_ministere: Column[str] = Column(
        String, ForeignKey("ref_ministere.code"), nullable=True
    )
    code_theme: Column[str] = Column(String, ForeignKey("ref_theme.code"), nullable=True)
    theme: Column[int] = Column(Integer, ForeignKey("ref_theme.id"), nullable=True)

    label: Column[str] = Column(String)
    description: Column[str] = Column(Text)

    theme_r: Mapped[Theme] = relationship("Theme", uselist=False, lazy="select", foreign_keys=code_theme)
    # permet de remonter uniquement le label
    label_theme = association_proxy("theme_r", "label")

    def __setattr__(self, key, value):
        """
        Intercept attribute setting for the instance.

        If the attribute being set is 'code' and the value is a string
        starting with '0', this method removes the first character.

        Args:
            key (str): The name of the attribute being set.
            value: The value to set the attribute to.

        Returns:
            None.

        Raises:
            TypeError: If the attribute being set is 'code' and the value
                is not a string.

        """
        if key == "code" and isinstance(value, str) and value.startswith("0"):
            value = value[1:]  # Remove the first character
        super().__setattr__(key, value)
