from flask import Blueprint, jsonify, request
from app.services.cart_service import rent_cart as rent_cart_service
from app.services.cart_service import return_cart as return_cart_service
from app.schemas.cart_schema import cart_schema

cart_bp = Blueprint('cart', __name__)

@cart_bp.route('/rent', methods=['POST'])
def rent_cart():
    """
    카트 대여
    ---
    tags:
      - Cart
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            user_id:
              type: integer
              example: 1
            cart_id:
              type: integer
              example: 1
          required:
            - user_id
            - cart_id
    responses:
        200:
            description: 대여 성공
        400:
            description: 잘못된 요청
        404:
            description: 카트 없음
    """
    data = request.get_json() or {}
    user_id = data.get('user_id')
    cart_id = data.get('cart_id')

    try:
        cart = rent_cart_service(user_id, cart_id)

        serialized_cart = cart_schema.dump(cart)

        return jsonify({
            "message": "cart rented successfully",
            "cart": serialized_cart
        }), 200

    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": "서버 내부 에러가 발생했습니다."}), 500


@cart_bp.route('/return', methods=['POST'])
def return_cart():
    """
    카트 반납
    ---
    tags:
      - Cart
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            cart_id:
              type: integer
              example: 1
          required:
            - cart_id
    responses:
      200:
        description: 반납 성공
      400:
        description: 잘못된 요청
      404:
        description: 카트 없음
    """
    data = request.get_json() or {}
    cart_id = data.get('cart_id')
    try:
        cart = return_cart_service(cart_id)

        serialized_cart = cart_schema.dump(cart)

        return jsonify({
            "message": "cart returned successfully",
            "cart": serialized_cart
        }), 200

    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": "서버 내부 에러가 발생했습니다."}), 500