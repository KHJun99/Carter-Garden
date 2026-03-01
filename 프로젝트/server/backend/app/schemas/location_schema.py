from app.extensions import ma
from app.models.location import Location

class LocationSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Location
        load_instance = True
        ordered = True

location_schema = LocationSchema()
locations_schema = LocationSchema(many=True)
