from marshmallow import Schema, fields, validate, ValidationError


def not_blank(value):
    if value is not None and not str(value).strip():
        raise ValidationError("Name cannot be blank if provided.")


class ClientSchema(Schema):
    """Schema for validating and serializing Client entities."""

    id = fields.Int(dump_only=True)
    name = fields.Str(
        required=False,
        allow_none=True,
        validate=[validate.Length(max=120), not_blank],
        metadata={"description": "Client's full name"},
    )
    email = fields.Email(
        required=False,
        allow_none=True,
        validate=validate.Length(max=120),
        metadata={"description": "Client's email address"},
    )
    phone = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(max=30),
        metadata={"description": "Client's phone number"},
    )
    created_at = fields.DateTime(dump_only=True)

    # Add more fields as needed, matching your Client model
