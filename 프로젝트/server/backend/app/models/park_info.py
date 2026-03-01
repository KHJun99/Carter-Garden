from app.extensions import db
from datetime import datetime

class ParkInfo(db.Model):
    __tablename__ = 'park_info'
    
    park_info_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    location_id = db.Column(db.BigInteger, db.ForeignKey('locations.location_id'), nullable=True)
    car_number = db.Column(db.String(20), nullable=False)
    entry_time = db.Column(db.DateTime, default=datetime.now)

    location = db.relationship('Location', backref='park_infos')
