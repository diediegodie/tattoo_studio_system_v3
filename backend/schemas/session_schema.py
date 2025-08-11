from marshmallow import Schema, fields


class SessionSchema(Schema):
    id = fields.Int(dump_only=True)
    artist_id = fields.Int(required=True)
    client_id = fields.Int(required=True)
    date = fields.Date(required=True)
    start_time = fields.Time(required=True)
    end_time = fields.Time(required=True)
    notes = fields.Str(allow_none=True)
