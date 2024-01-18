import pytest
from app.utilities.siret import SiretFormatError, SiretParser


def test_parse_siret_ok():
    parser = SiretParser("26350579400028")
    _assert_parser_good_siret_siren(parser)

    assert "263505794" == parser.siren, "Le siren doit être égal à celui fourni"
    assert "26350579400028" == parser.siret, "Le siret doit être égal à celui fourni"


def test_parse_siren_ok():
    parser = SiretParser("263505794", raise_on_siren=False)
    _assert_parser_good_siret_siren(parser)

    assert "263505794" == parser.siren, "Le siren doit être égal à celui fourni"
    assert "26350579400000" == parser.siret, "Le siret doit être égal à celui fourni"


@pytest.mark.parametrize(
    "invalid_siret",
    [
        ("263505794"),
        ("aaaaaaaaa"),
        ("11"),
        (""),
        (None),
    ],
)
def test_parse_invalid_siret(invalid_siret):
    with pytest.raises(SiretFormatError):
        SiretParser(invalid_siret)


def test_is_siret_valide_util_function():
    ut = "263505794"
    assert not SiretParser.is_siret_valide(ut), f"Le siret {ut} ne devrait pas être validé"

    ut = "26350579400000"
    assert SiretParser.is_siret_valide(ut), f"Le siret {ut} devrait être validé"


def _assert_parser_good_siret_siren(parser: SiretParser):
    _assert_siren_is_9_len(parser.siren)
    _assert_siret_is_14_len(parser.siret)


def _assert_siret_is_14_len(siret: str):
    assert len(siret) == 14, f"Le siret {siret} devrait être long de 14 caractères"


def _assert_siren_is_9_len(siren: str):
    assert len(siren) == 9, f"Le siren {siren} devrait être long de 14 caractères"
