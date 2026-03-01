from app.extensions import db

class Coupon(db.Model):
    __tablename__ = 'coupons'
    
    coupon_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.user_id'), nullable=False)
    coupon_name = db.Column(db.String(100), nullable=False)
    discount_amount = db.Column(db.Integer, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    expire_date = db.Column(db.DateTime)

    def __repr__(self):
        return f'<Coupon {self.coupon_name}: {self.discount_amount}원>'
