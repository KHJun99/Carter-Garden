from app.extensions import db

class Location(db.Model):
    __tablename__ = 'locations'
    
    location_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    location_code = db.Column(db.String(20), nullable=False, unique=True)
    category = db.Column(db.String(20), nullable=False)
    pos_x = db.Column(db.Float, nullable=False)
    pos_y = db.Column(db.Float, nullable=False)

class LocationPath(db.Model):
    __tablename__ = 'location_paths'
    
    path_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    node1_id = db.Column(db.BigInteger, db.ForeignKey('locations.location_id'), nullable=False)
    node2_id = db.Column(db.BigInteger, db.ForeignKey('locations.location_id'), nullable=False)
