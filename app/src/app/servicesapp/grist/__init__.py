from models.exceptions import DataRegatException


class ParsingColumnsError(DataRegatException):
    def __init__(self):
        self.message = "Les lignes n'ont pas les même colonne"
        super().__init__()