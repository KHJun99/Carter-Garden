from app.models.coupon import Coupon
from app.extensions import db
from app.utils.time import get_current_time, is_expired

def get_user_coupons(user_id):
    now = get_current_time()
    # 사용하지 않았고, 만료 전인 쿠폰만 필터링
    return Coupon.query.filter(
        Coupon.user_id == user_id,
        Coupon.is_used == False,
        Coupon.expire_date > now
    ).order_by(Coupon.expire_date.asc()).all()

def use_coupon(coupon_id):
    coupon = Coupon.query.get(coupon_id)
    if not coupon:
        raise ValueError("Coupon not found")
    if coupon.is_used:
        raise ValueError("Coupon has already been used")
    if is_expired(coupon.expire_date):
        raise ValueError("Coupon has expired")
    # 쿠폰 사용 처리
    coupon.is_used = True
    db.session.commit()
    return coupon