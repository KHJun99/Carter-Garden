from app.models.location import Location

def get_all_locations():
    return Location.query.all()

def get_location_by_code(code):
    return Location.query.filter_by(location_code=code).first()

def get_locations_by_category(category):
    return Location.query.filter_by(category=category).all()
