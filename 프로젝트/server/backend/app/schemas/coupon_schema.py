from marshmallow import Schema, fields
from app.utils.time import format_datetime

class CouponSchema(Schema):
    coupon_id = fields.Integer(dump_only=True)
    user_id = fields.Integer(required=True)
    coupon_name = fields.String()
    discount_amount = fields.Integer()
    is_used = fields.Boolean()

    expire_date = fields.Function(lambda obj: format_datetime(obj.expire_date))

# 인스턴스 생성
coupon_schema = CouponSchema()
coupons_schema = CouponSchema(many=True)
