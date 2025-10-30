"""
Module qui représente les schemas marshmallow associés aux différents modèles.
"""

# ruff: noqa: F401
from .audit import AuditUpdateDataSchema
from .tags import TagsSchema
from .demarches import (
    DemarcheSchema,
    DonneeSchema,
    DossierSchema,
    ReconciliationSchema,
    SectionSchema,
    TypeSchema,
    ValeurDonneeSchema,
)
from .financial import (
    AdemeSchema,
    FinancialAeSchema,
    FinancialCpSchema,
    EnrichedFlattenFinancialLinesSchema,
    FlattenFinancialLinesDataQpvSchema
)
from .preferences import (
    PreferenceFormSchema,
    ShareSchema,
    SharesFormSchema,
    PreferenceSchema,
)
from .refs import (
    QpvSchema,
    SiretSchema,
    CommuneSchema,
    MinistereSchema,
    CentreCoutsSchema,
    ThemeSchema,
    CodeProgrammeSchema,
    ArrondissementSchema,
    GroupeMarchandiseSchema,
    DomaineFonctionnelSchema,
    ReferentielProgrammationSchema,
    LocalisationInterministerielleSchema,
)
from .visuterritoire import France2030Schema, MontantParNiveauBopAnneeTypeSchema
from .common import DataTypeField
