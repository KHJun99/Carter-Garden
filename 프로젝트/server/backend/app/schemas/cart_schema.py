from marshmallow import Schema, fields

class CartSchema(Schema):
    cart_id = fields.Integer(dump_only=True) # 서버에서 생성하므로 dump_only
    user_id = fields.Integer(allow_none=True) # 사용 중이지 않을 수 있으므로
    status = fields.String()

# 단건 조회 및 리스트 조회용 인스턴스
cart_schema = CartSchema()