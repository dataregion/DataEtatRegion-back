import logging
import dataclasses
from app import db
from app.models.financial.FinancialAe import FinancialAe as Ae
from app.models.tags.Tags import TagVO, TagAssociation
from app.models.tags.Tags import Tags as DbTag
from sqlalchemy import delete, and_, select

logger = logging.getLogger(__name__)


def select_tag(tag: TagVO) -> DbTag:
    """
    Retourne l'objet DbTag à partir du type et de la valeur
    :param tag:    un tag value object
    :return:
    le Tag
    """
    stmt = db.select(DbTag)
    stmt = stmt.where(DbTag.type == tag.type)
    if tag.value is not None:
        stmt = stmt.where(DbTag.value == tag.value)

    return db.session.execute(stmt).scalar_one()


def select_tags(tags: list[TagVO]) -> list[DbTag]:
    db_tags = [select_tag(tag) for tag in tags]
    return db_tags


def _select_ae_having_tags(tag_id: int):
    """
    Retourne la selection d'ae qui ont déjà au moins un tag tag_id appliqué
    :param tag_id: l'id du tag
    :return:
    """
    return db.select(TagAssociation.financial_ae).where(TagAssociation.tag_id == tag_id).distinct()


@dataclasses.dataclass
class ApplyTagForAutomation:
    tag: DbTag

    def apply_tags_ae(self, whereclause):
        """
        Applique un tag sur les Financial AE retournée par le statement passé en paramètre
        :param tag: le tag à appliquer
        :param where_clause: le filtrage
        :return:
        """
        stmt_ae = db.select(Ae.id).where(whereclause).where(Ae.id.not_in(_select_ae_having_tags(self.tag.id)))
        ae_ids = [row[0] for row in db.session.execute(stmt_ae).all()]

        # on vérifie que la liste des lignes à ajouter est non vide. Sinon pas besoin d'insert de nouvelle Assocations
        if ae_ids:
            for ae_id in ae_ids:
                db.session.add(TagAssociation(financial_ae=ae_id, tag=self.tag, auto_applied=True))
            db.session.commit()
            logger.info(f"[TAGS][{self.tag.type}] Fin application auto du tags")
        else:
            logger.info(f"[TAGS][{self.tag.type}] Aucune nouvelle association détecté")


@dataclasses.dataclass
class PutOnAeResult:
    deleted: int
    created: int


@dataclasses.dataclass
class ApplyManualTags:
    tags: list[DbTag]

    def put_on_ae(self, n_ej: str, poste_ej: str) -> PutOnAeResult:
        """
        Annule et remplace les tags associés à un AE identifié par son numero ej et poste ej.
        """
        process_result = PutOnAeResult(0, 0)
        logger.debug(
            f"Annule et remplace les tags de l'ae(n_ej, poste_ej) = ({n_ej, poste_ej}) pour les tags [{self.tags}])"
        )

        _ae_n_ej_and_poste_ej_eq = and_(Ae.n_ej == str(n_ej), Ae.n_poste_ej == int(poste_ej))

        delete_stmt = (
            delete(TagAssociation)
            .where(_ae_n_ej_and_poste_ej_eq)
            .where(Ae.id == TagAssociation.financial_ae)
            .where(TagAssociation.auto_applied == False)
        )

        result = db.session.execute(delete_stmt)
        logger.debug(f"Suppression des anciens tags ({result.rowcount} associations)")
        process_result.deleted = result.rowcount

        list_ae_stmt = select(Ae).where(_ae_n_ej_and_poste_ej_eq)

        associations = []
        result = db.session.execute(list_ae_stmt)
        rows = result.fetchall()
        for row in rows:
            ae = row[0]
            for db_tag in self.tags:
                association = TagAssociation(financial_ae=ae.id, tag=db_tag, auto_applied=False)
                associations.append(association)

        len_associations = len(associations)
        logger.debug(f"Creating {len_associations} associations")
        for association in associations:
            db.session.add(association)
        process_result.created = len_associations

        db.session.commit()
        return process_result
