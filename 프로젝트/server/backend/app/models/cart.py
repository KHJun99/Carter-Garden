from app.extensions import db

class Cart(db.Model):
    __tablename__ = 'carts'
    
    cart_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.user_id'), nullable=True)
    status = db.Column(db.String(20), default='WAITING')

    def __repr__(self):
        return f'<Cart {self.cart_id}: {self.status}>'
