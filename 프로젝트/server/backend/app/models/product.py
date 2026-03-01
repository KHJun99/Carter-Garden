from app.extensions import db

class Category(db.Model):
    __tablename__ = 'categories'
    
    category_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    category_name = db.Column(db.String(50), nullable=False)

class Product(db.Model):
    __tablename__ = 'products'
    
    product_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    category_id = db.Column(db.BigInteger, db.ForeignKey('categories.category_id'), nullable=False)
    location_id = db.Column(db.BigInteger, db.ForeignKey('locations.location_id'), nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    image_url = db.Column(db.String(255))
    description = db.Column(db.Text)
    amount = db.Column(db.Integer, default=0)

    category = db.relationship('Category', backref='products')
    location = db.relationship('Location', backref='products')
