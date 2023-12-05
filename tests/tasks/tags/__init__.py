__all__ = (
    "TAG_FOND_VERT",
    "TAG_DISABLE_AUTO",
    "TAG_RELANCE",
    "TAG_DUMMY",
    "TAG_DETR",
    "TAG_CPER_15_20",
    "TAG_CPER_21_27",
    "TAG_PVD",
    "TAG_ACV",
)

from faker import Faker


TAG_FOND_VERT = {
    "type": "fonds-vert",
    "value": None,
    "description": "Tag auto Fond Vert si programme = 380",
    "display_name": "Fonds vert",
    "enable_rules_auto": True,
}

TAG_DISABLE_AUTO = {
    "type": "test",
    "value": None,
    "description": "tag non actif",
    "display_name": "Test",
    "enable_rules_auto": False,
}

TAG_RELANCE = {
    "type": "relance",
    "value": None,
    "description": "relance",
    "display_name": "Relance",
    "enable_rules_auto": True,
}

TAG_DETR = {
    "type": "detr",
    "value": None,
    "description": "detr",
    "display_name": "DETR",
    "enable_rules_auto": True,
}

TAG_DUMMY = {
    "type": "tag_dummy",
    "value": None,
    "description": "tag dummy",
    "display_name": "Tag dummy",
    "enable_rules_auto": True,
}

TAG_CPER_15_20 = {
    "type": "cper",
    "value": "2015-20",
    "description": "tag cper",
    "display_name": "CPER:2015-20",
    "enable_rules_auto": True,
}

TAG_CPER_21_27 = {
    "type": "cper",
    "value": "2021-27",
    "description": "tag cper",
    "display_name": "CPER:2021-27",
    "enable_rules_auto": True,
}

TAG_PVD = {
    "type": "pvd",
    "value": None,
    "description": "tag pvd",
    "display_name": "PVD",
    "enable_rules_auto": True,
}

TAG_ACV = {
    "type": "acv",
    "value": None,
    "description": "tag acv",
    "display_name": "ACV",
    "enable_rules_auto": True,
}

def faked_tag_json(faker: Faker):
    """Génère un JSON représentant un tag random"""
    return {
        "type": faker.pystr(),
        "value": faker.boolean() and faker.pystr() or None,
        "description": faker.pystr(),
        "enable_rules_auto": faker.boolean(),
    }
