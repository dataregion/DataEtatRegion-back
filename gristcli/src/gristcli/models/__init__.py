class UserGrist:
    def __init__(
        self, username: str, display_name: str, email: str, user_id: str = None
    ):
        self.user_id = user_id
        self.username = username
        self.display_name = display_name
        self.email = email

    def __repr__(self):
        return f"UserGrist(user_id={self.user_id}, username={self.username}, display_name={self.display_name}, email={self.email}"

    def to_scim_payload(self):
        """
        Convertit un objet UserGrist en un dictionnaire respectant le modèle SCIM pour l'API Grist.
        """
        return {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "userName": self.username,
            "name": {"formatted": self.display_name},
            "emails": [{"value": self.email, "primary": True}],
            "displayName": self.display_name,
            "preferredLanguage": "fr",
            "locale": "fr",
        }
    
class Document:
    def __init__(self, **kwargs):
        self.id = kwargs.pop("id", None)
        self.name = kwargs.pop("name", None)
        self.access = kwargs.pop("access", None)
        self.isPinned = kwargs.pop("isPinned", None)
        self.urlId = kwargs.pop("urlId", None)

    def __repr__(self):
        return f"Document(id={self.id}, name={self.name}, access={self.access})"


class Workspace:
    def __init__(self, **kwargs):
        self.id = kwargs.pop("id", None)
        self.name = kwargs.pop("name", None)
        self.access = kwargs.pop("access", None)
        self.orgDomain = kwargs.pop("orgDomain", None)
        self.docs = [Document(**doc) for doc in kwargs.pop("docs", [])]

    def __repr__(self):
        return f"Workspace(id={self.id}, name={self.name}, docs={self.docs})"
