import logging

from sqlalchemy import and_

from app import db
from models.entities.demarches.Token import Token

logger = logging.getLogger(__name__)


class TokenService:
    @staticmethod
    def find_by_uuid_utilisateur(uuid_utilisateur: str) -> list[Token]:
        stmt = db.select(Token).where(Token.uuid_utilisateur == uuid_utilisateur)
        return db.session.execute(stmt).scalars().all()

    @staticmethod
    def find_by_uuid_utilisateur_and_token_id(uuid_utilisateur: str, token_id: int) -> Token:
        return (
            db.session.query(Token).filter(and_(Token.uuid_utilisateur == uuid_utilisateur, Token.id == token_id)).one()
        )

    @staticmethod
    def create(nom: str, token_value: str, uuid_utilisateur: str) -> Token:
        token = Token(nom=nom, token=token_value, uuid_utilisateur=uuid_utilisateur)
        db.session.add(token)
        db.session.commit()
        return token

    @staticmethod
    def update(token_id: int, nom: str, token_value: str, uuid_utilisateur: str) -> Token:
        token = (
            db.session.query(Token).filter(and_(Token.id == token_id, Token.uuid_utilisateur == uuid_utilisateur)).one()
        )
        token.nom = nom
        token.token = token_value
        db.session.commit()
        return token

    @staticmethod
    def delete(token_id: int, uuid_utilisateur: str):
        db.session.query(Token).filter(and_(Token.id == token_id, Token.uuid_utilisateur == uuid_utilisateur)).delete()
        db.session.commit()
