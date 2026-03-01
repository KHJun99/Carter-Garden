# User service logic
from app.models.user import User
from flask_jwt_extended import create_access_token
from app.utils.response import error_response, success_response

def login_service(data):
    login_id = data.get('login_id')
    password = data.get('password')

    # 1. 사용자 조회
    user = User.query.filter_by(login_id=login_id).first()

    # 2. 사용자 없음 또는 비밀번호 불일치
    if not user or not user.check_password(password):
        return error_response("아이디 또는 비밀번호가 올바르지 않습니다.", 401)

    # ============================================================
    # [수정 핵심] identity는 반드시 '문자열(str)'이어야 합니다!
    # user.user_id (int) -> str(user.user_id) 로 변경
    # ============================================================
    access_token = create_access_token(identity=str(user.user_id))

    return success_response(
        data={
            "access_token": access_token,
            "user_name": user.user_name,
            "user_id": user.user_id
        },
        message="로그인 성공"
    )

def get_user_info_service(user_id):
    # DB 조회 시에는 문자열 "1"이 들어가도 알아서 숫자로 처리해주니 걱정 안 해도 됩니다.
    user = User.query.get(user_id)
    if not user:
        return error_response("사용자를 찾을 수 없습니다.", 404)

    return success_response(data=user.to_dict())