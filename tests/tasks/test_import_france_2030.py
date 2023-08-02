import os
from unittest.mock import patch, call

from app.tasks.financial.import_france_2030 import import_file_france_2030


def test_import_import_file():
    #DO
    with patch('shutil.move', return_value=None): #ne pas supprimer le fichier de tests :)
        import_file_france_2030(os.path.abspath(os.getcwd()) + '/data/france_2030.xlsx')