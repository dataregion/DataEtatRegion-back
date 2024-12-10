import logging

from sqlalchemy import and_

from app import db
from models.entities.demarches.Token import Token

logger = logging.getLogger(__name__)


class TokenService:
    @staticmethod
    def find_enabled_by_uuid_utilisateur(uuid_utilisateur: str) -> list[Token]:
        stmt = db.select(Token).where(Token.uuid_utilisateur == uuid_utilisateur, Token.enabled == True)  # noqa: E712
        return db.session.execute(stmt).scalars().all()

    @staticmethod
    def find_by_uuid_utilisateur_and_token_id(uuid_utilisateur: str, token_id: int) -> Token:
        return (
            db.session.query(Token).filter(and_(Token.uuid_utilisateur == uuid_utilisateur, Token.id == token_id)).one()
        )

    @staticmethod
    def find_by_uuid_utilisateur_and_token_value(uuid_utilisateur: str, token_value: str) -> Token:
        # Récupération des tokens de l'utilisateur, puis ensuite filtre sur le token une fois decrypté
        tokens = [
            t
            for t in (db.session.query(Token).filter(and_(Token.uuid_utilisateur == uuid_utilisateur)).all())
            if t.token == token_value
        ]
        return tokens[0] if len(tokens) == 1 else None

    @staticmethod
    def create(nom: str, token_value: str, uuid_user: str) -> Token:
        # Vérification de l'existence du token
        token = TokenService.find_by_uuid_utilisateur_and_token_value(uuid_user, token_value)

        # Si le token existe mais est juste soft-disabled, on renomme et réactive
        if token is not None and token.enabled is False:
            db.session.execute(db.update(Token).where(Token.id == token.id).values(dict(nom=nom, enabled=True)))
            db.session.commit()
            return token

        # Sinon, création du token
        token = Token(nom=nom, token=token_value, uuid_utilisateur=uuid_user)
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
    def delete(token_id: int, uuid_user: str):
        # Désactivation du token
        db.session.execute(
            db.update(Token).where(Token.id == token_id, Token.uuid_utilisateur == uuid_user).values(enabled=False)
        )
        db.session.commit()
