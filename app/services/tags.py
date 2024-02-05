import logging
import dataclasses
from more_itertools import ichunked
from app import db
from app.models.financial import FinancialData
from app.models.financial.FinancialAe import FinancialAe as Ae
from app.models.financial.FinancialCp import FinancialCp as Cp
from app.models.financial.Ademe import Ademe
from app.models.tags.Tags import TagVO, TagAssociation, Tags
from app.models.tags.Tags import Tags as DbTag
from sqlalchemy import Column, delete, and_, select, insert, join

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


def delete_associations_of_tag(tag: DbTag):
    stmt = delete(TagAssociation).where(TagAssociation.tag_id == tag.id)
    result = db.session.execute(stmt)
    db.session.commit()
    return result.rowcount


def _tag_association_column_corresponding_to_financial_entity_type(
    financial_entity_type: type[FinancialData],
) -> Column[int]:
    if financial_entity_type == Ademe:
        return TagAssociation.ademe
    elif financial_entity_type == Ae:
        return TagAssociation.financial_ae
    elif financial_entity_type == Cp:
        return TagAssociation.financial_cp
    else:
        raise NotImplementedError(
            "Impossible de créer une association de tag pour l'entité"
            f" de type {financial_entity_type.__class__.__name__}"
        )


def _select_financial_entity_ids_having_tags(tag_id: int, financial_entity_type: type[FinancialData]):
    """
    Retourne la selection d'entités financières qui ont déjà au moins un tag tag_id appliqué
    :param tag_id: l'id du tag
    :param financial_entity_type: le type d'entité financière
    :return:
    """
    column = _tag_association_column_corresponding_to_financial_entity_type(financial_entity_type)
    stmt = db.select(column).where(TagAssociation.tag_id == tag_id).distinct()
    return stmt


def _new_tag_association(financial_entity_type: type[FinancialData], id: int, tag: Tags):
    """Crée une association de tag pour une entité de donnée financière"""
    association = TagAssociation()
    association.tag_id = tag.id

    fk_column = _tag_association_column_corresponding_to_financial_entity_type(financial_entity_type)
    setattr(association, fk_column.key, id)

    return association


@dataclasses.dataclass
class ApplyTagForAutomation:
    tag: DbTag

    def _apply_tags_entity(self, whereclause, financial_entity_type: type[FinancialData]):
        """
        Applique un tag sur les entités financières retournées par le statement passé en paramètre
        :param tag: le tag à appliquer
        :param where_clause: le filtrage
        :param entity_type: le type d'entité financière
        :return:
        """
        # Selectionne les entités financières éligibles au tag auto qui n'ont pas d'association existantes
        ta_column = _tag_association_column_corresponding_to_financial_entity_type(financial_entity_type)
        stmt_entity_ids = (
            db.select(financial_entity_type.id)
            .select_from(
                join(
                    financial_entity_type,
                    TagAssociation,
                    (financial_entity_type.id == ta_column) & (TagAssociation.tag_id == self.tag.id),
                    isouter=True,
                )
            )
            .where(whereclause)
            .where(TagAssociation.id.is_(None))
        )

        #
        entity_ids = [row[0] for row in db.session.execute(stmt_entity_ids).all()]

        if len(entity_ids) == 0:
            logger.info(f"[TAGS][{self.tag.type}] Aucune nouvelle association détecté")
            return self

        chunks = ichunked(entity_ids, 10_000)
        for chunk in chunks:
            # on vérifie que la liste des lignes à ajouter est non vide. Sinon pas besoin d'insert de nouvelle Assocations
            insert_to_commit = []
            for entity_id in chunk:
                association = _new_tag_association(financial_entity_type, entity_id, self.tag)
                association.auto_applied = True  # type: ignore

                insert_to_commit.append(
                    {
                        TagAssociation.financial_ae.name: association.financial_ae,
                        TagAssociation.financial_cp.name: association.financial_cp,
                        TagAssociation.ademe.name: association.ademe,
                        TagAssociation.tag_id.name: association.tag_id,
                        TagAssociation.auto_applied.name: association.auto_applied,
                    }
                )
            db.session.execute(insert(TagAssociation), insert_to_commit)

        db.session.commit()
        logger.info(f"[TAGS][{self.tag.type}] Fin application auto du tags : {len(entity_ids)}")

        return self

    def apply_tags_ae(self, whereclause):
        """
        Applique un tag sur les Financial AE retournée par le statement passé en paramètre
        :param tag: le tag à appliquer
        :param where_clause: le filtrage
        :return:
        """
        return self._apply_tags_entity(whereclause, Ae)

    def apply_tags_cp(self, whereclause):
        """
        Applique un tag sur les Financial CP retournée par le statement passé en paramètre
        :param tag: le tag à appliquer
        :param where_clause: le filtrage
        :return:
        """
        return self._apply_tags_entity(whereclause, Cp)


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
            .where(TagAssociation.auto_applied == False)  # noqa: E712
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
