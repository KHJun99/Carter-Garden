from flask import Blueprint, jsonify
from app.services.coupon_service import get_user_coupons as get_user_coupons_service
from app.services.coupon_service import use_coupon as use_coupon_service
from app.schemas.coupon_schema import coupon_schema, coupons_schema

coupon_bp = Blueprint('coupon', __name__)

@coupon_bp.route('/<int:user_id>', methods=['GET'])
def get_user_coupons(user_id):
    """
    유저 쿠폰 리스트 조회
    ---
    tags:
      - Coupon
    parameters:
      - in: path
        name: user_id
        required: true
        type: integer
        example: 1
    responses:
        200:
            description: 쿠폰 리스트 조회 성공
    """
    coupons = get_user_coupons_service(user_id)
    return jsonify({
        "user_id": user_id,
        "coupons": coupons_schema.dump(coupons),
        "message": "coupon list fetched successfully"
    }), 200

@coupon_bp.route('/use/<int:coupon_id>', methods=['POST'])
def use_coupon(coupon_id):
    """
    쿠폰 사용
    ---
    tags:
      - Coupon
    parameters:
        - in: path
          name: coupon_id
          required: true
          type: integer
          example: 1
    responses:
        200:
            description: 쿠폰 사용 성공
    """
    try:
        # 서비스에서 쿠폰 사용 로직 실행
        coupon = use_coupon_service(coupon_id)

        # 업데이트된 쿠폰 객체를 직렬화
        serialized_coupon = coupon_schema.dump(coupon)

        return jsonify({
            "message": "coupon used successfully",
            "coupon": serialized_coupon
        }), 200

    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": "서버 내부 에러가 발생했습니다."}), 500