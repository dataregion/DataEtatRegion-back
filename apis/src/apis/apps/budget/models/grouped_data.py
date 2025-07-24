class GroupedData:

    def __init__(
        self,
        colonne: str,
        total: int,
        total_montant_engage: float,
        total_montant_paye: float
    ):
        self.colonne = colonne
        self.total = total
        self.total_montant_engage = total_montant_engage
        self.total_montant_paye = total_montant_paye

    def to_dict(self):
        return {
            "colonne": self.colonne,
            "total": self.total,
            "total_montant_engage": self.total_montant_engage,
            "total_montant_paye": self.total_montant_paye
        }