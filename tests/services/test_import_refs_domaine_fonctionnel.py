import json
import os
import pytest
from unittest.mock import patch, call

from app.models.refs.domaine_fonctionnel import DomaineFonctionnel
from app.services import MissingCodeColumns, import_refs, ReferentielNotFound, import_line_one_ref


def test_import_refs_with_missing_code_column(app):
    """Test that import_refs raises MissingCodeColumns exception when 'Code' column is missing."""
    with pytest.raises(MissingCodeColumns):
        import_refs('tests/data/domaine_fonctionnel.xls', 'MyModel', ['Name', 'Description', 'Value'])

def test_import_refs_with_referential_not_found(app):
    """Test that import_refs raises ReferentielNotFound exception when the referential file is not found."""
    with pytest.raises(ReferentielNotFound):
        import_refs('tests/data/non_existing.csv', 'MyModel', ['code', 'Name', 'Description', 'Value'])

def test_import_line_ref_with_referential_not_found(app):
    """Test that import_refs raises ReferentielNotFound exception when the referential file is not found."""
    with pytest.raises(ReferentielNotFound):
        import_line_one_ref('NotModel', '')

@patch('app.services.import_refs.subtask')
def test_import_refs_domaine_fonctionnel(mock_subtask,test_db):
    import_refs(os.path.abspath(os.getcwd())+'/data/Calculette_Chorus_test.xlsx', 'DomaineFonctionnel',
                ['code', 'label'], is_csv=False, usecols=[4,5],
                sheet_name="07 - Domaines Fonct. (DF)", skiprows=8)
    mock_subtask.assert_has_calls([
        call().delay('DomaineFonctionnel', '{"code":"0104-12-08","label":"TEST"}'),
        call().delay('DomaineFonctionnel', '{"code":"0104-12-15","label":"Actions R\\u00e9fugi\\u00e9s"}'),
        call('import_line_one_ref'),
    ], any_order=True)


def test_import_line_ref_with_attribute_error(app):
    # Given
    code = '123'
    row = json.dumps({'code': code, 'name': 'Test'})
    # When
    with pytest.raises(TypeError):
        import_line_one_ref('DomaineFonctionnel', row)

def test_import_new_line_domaine_fonctionnel(app):
    # Given
    code = '123'
    row = json.dumps({'code': code, 'label': 'Test'})
    # When
    import_line_one_ref('DomaineFonctionnel', row)

    # Then
    with app.app_context():
        d = DomaineFonctionnel.query.filter_by(code=code).one()
        assert d.code == code
        assert d.label == "Test"

def test_import_update_domaine_fonctionnel_line(app, test_db):
    #Given
    update_dommaine = DomaineFonctionnel(code="xxx", label="to_update")
    with app.app_context():
        test_db.session.add(update_dommaine)

    # When
    import_line_one_ref('DomaineFonctionnel', json.dumps({'code': 'xxx', 'label': 'label_updating'}))
    import_line_one_ref('DomaineFonctionnel', json.dumps({'code': 'yyy', 'label': 'Actions R\\u00e9fugi\\u00e9s'}))
    with app.app_context():
        d_to_update = DomaineFonctionnel.query.filter_by(code='xxx').one()
        assert d_to_update.label == "label_updating"
        d_new = DomaineFonctionnel.query.filter_by(code='yyy').one()
        assert d_new.label == "Actions Réfugiés"



