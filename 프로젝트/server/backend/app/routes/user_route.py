from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.user_service import login_service, get_user_info_service
from app.schemas.user_schema import LoginSchema

user_bp = Blueprint('user', __name__, url_prefix='/users')

@user_bp.route('/login', methods=['POST'])
def login():
    """
    유저 로그인
    ---
    tags:
      - User
    description: 아이디와 비밀번호를 입력하여 JWT 토큰을 발급받습니다.
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - login_id
            - password
          properties:
            login_id:
              type: string
              example: test
              description: 로그인 아이디
            password:
              type: string
              example: "1234"
              description: 비밀번호
    responses:
      200:
        description: 로그인 성공
        schema:
          type: object
          properties:
            result:
              type: string
              example: success
            message:
              type: string
            data:
              type: object
              properties:
                access_token:
                  type: string
                  description: 발급된 JWT 토큰
                user_name:
                  type: string
                user_id:
                  type: integer
      401:
        description: 로그인 실패
    """
    # 데이터 검증
    schema = LoginSchema()
    errors = schema.validate(request.json)
    if errors:
        return jsonify({"result": "fail", "message": str(errors)}), 400

    # 서비스 호출
    return login_service(request.json)

@user_bp.route('/me', methods=['GET'])
@jwt_required()
def get_my_info():
    """
    내 정보 조회 (JWT 필수)
    ---
    tags:
      - User
    description: 헤더에 있는 JWT 토큰을 해석하여 현재 로그인한 유저의 정보를 반환합니다.
    security:
      - Bearer: []
    responses:
      200:
        description: 조회 성공
        schema:
          type: object
          properties:
            result:
              type: string
              example: success
            data:
              type: object
              properties:
                user_id:
                  type: integer
                user_name:
                  type: string
                login_id:
                  type: string
      401:
        description: 인증 실패
    """
    current_user_id = get_jwt_identity()
    return get_user_info_service(current_user_id)