from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from models.entities.preferences.Preference import Preference, Share


class SharesFormSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Share
        exclude = (
            "id",
            "email_send",
        )

    shared_username_email = fields.Email(required=True)


class PreferenceFormSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Preference
        exclude = (
            "uuid",
            "date_creation",
            "nombre_utilisation",
            "dernier_acces",
            "application_host",
            "application_clientid",
        )

    filters = fields.Raw(required=True)
    shares = fields.List(fields.Nested(SharesFormSchema), required=False)


class ShareSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Share
        exclude = (
            "id",
            "preference_id",
        )


class PreferenceSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Preference
        exclude = (
            "id",
            "date_creation",
            "nombre_utilisation",
            "dernier_acces",
        )

    shares = fields.List(fields.Nested(ShareSchema), required=False)