
from app import db
from app.models.demarches.section import Section

class SectionService:

    @staticmethod
    def get_or_create(section_name: str) -> Section:
        """
        Retourne une section (création si non présent en BDD)
        :param section_name: Nom de la section
        :return: Section
        """
        stmt = db.select(Section).where(Section.name == section_name)
        section = db.session.execute(stmt).scalar_one_or_none()
        if section is not None:
            return section
        section = Section(**{"name": section_name})
        db.session.add(section)
        db.session.flush()
        return section

