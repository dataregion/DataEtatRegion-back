from sqlalchemy import create_engine, text

class UserDatabaseService:
    def __init__(self, database_url):
        """Initialise le service avec un moteur SQLAlchemy."""
        self.engine = create_engine(database_url, pool_pre_ping=True) 

    def get_user_by_id(self, id: int):
        with self.engine.connect() as connection:
            result = connection.execute(text("SELECT id, name FROM users WHERE id = :id"), {"id": id})
            user = result.mappings().first()
        return dict(user) if user else None
    
    def update_api_key(self, user_id: int, new_api_key: str):
        """Met à jour la colonne api_key pour un utilisateur donné."""
        query = text("UPDATE users SET api_key = :api_key WHERE id = :id")
        with self.engine.connect() as connection:
            result = connection.execute(query, {"api_key": new_api_key, "id": user_id})
            connection.commit()  # Nécessaire pour valider la transaction
        return result.rowcount > 0

