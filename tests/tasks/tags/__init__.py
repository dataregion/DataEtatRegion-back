__all__ = ("TAG_FOND_VERT", "TAG_DISABLE_AUTO", "TAG_RELANCE", "TAG_DUMMY", "TAG_DETR")

TAG_FOND_VERT = {
    "type": "Fond vert",
    "value": None,
    "description": "Tag auto Fond Vert si programme = 380",
    "enable_rules_auto": True,
}

TAG_DISABLE_AUTO = {
    "type": "test",
    "value": None,
    "description": "tag non actif",
    "enable_rules_auto": False,
}

TAG_RELANCE = {
    "type": "relance",
    "value": None,
    "description": "relance",
    "enable_rules_auto": True,
}

TAG_DETR = {
    "type": "DETR",
    "value": None,
    "description": "detr",
    "enable_rules_auto": True,
}

TAG_DUMMY = {
    "type": "tag_dummy",
    "value": None,
    "description": "tag dummy",
    "enable_rules_auto": True,
}
