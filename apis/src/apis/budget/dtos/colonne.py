class Colonne:
    
    def __init__(
        self,
        code: str | None = None,
        label: str | None = None,
        type: str | None = None,
        default: bool = True
    ):
        self.code = code
        self.label = label
        self.type = type
        self.default = default

    def to_dict(self):
        return {
            "code": self.code,
            "label": self.label,
            "type": self.type,
            "default": self.default
        }