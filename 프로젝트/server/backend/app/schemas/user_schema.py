# app/schemas/auth_schema.py
# Marshmallow schemas for authentication
from marshmallow import Schema, fields, validate

class LoginSchema(Schema):
    login_id = fields.String(required=True, error_messages={"required": "아이디는 필수입니다."})
    password = fields.String(required=True, error_messages={"required": "비밀번호는 필수입니다."})

class UserResponseSchema(Schema):
    user_id = fields.Integer()
    user_name = fields.String()
    login_id = fields.String()
    profile_image_url = fields.String()
    phone_number = fields.String()