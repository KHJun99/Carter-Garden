from app.extensions import ma
from app.models.park_info import ParkInfo
from marshmallow import fields
from app.schemas.location_schema import LocationSchema

class ParkInfoSchema(ma.SQLAlchemyAutoSchema):
    location = fields.Nested(LocationSchema, only=("location_code", "pos_x", "pos_y", "category"))

    class Meta:
        model = ParkInfo
        load_instance = True
        include_fk = True

park_info_schema = ParkInfoSchema()
park_infos_schema = ParkInfoSchema(many=True)
