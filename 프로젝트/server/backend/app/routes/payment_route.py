from flask import Blueprint, request, redirect, current_app
from app.services.payment_service import confirm_payment

payment_bp = Blueprint('payment', __name__)

@payment_bp.route('/toss/success', methods=['GET'])
def toss_success():
    """
    토스 결제 성공 리다이렉트 처리
    ---
    tags:
      - Payment
    parameters:
      - in: query
        name: paymentKey
        type: string
        required: true
      - in: query
        name: orderId
        type: string
        required: true
      - in: query
        name: amount
        type: integer
        required: true
    responses:
        302:
            description: 프론트엔드로 리다이렉트
    """
    payment_key = request.args.get('paymentKey')
    order_id = request.args.get('orderId')
    amount = request.args.get('amount')

    # 요청 파라미터에서 'next_url' 받아오기
    next_url = request.args.get('next_url')

    # next_url이 없으면 에러 처리 (리다이렉트 불가)
    if not next_url:
        return {'code': 'FAIL', 'message': 'Next URL is missing'}, 400

    # Service Layer 호출
    res_json, status_code = confirm_payment(payment_key, order_id, amount)

    if status_code == 200:
        return redirect(f"{next_url}/finish?orderId={order_id}")
    else:
        error_msg = res_json.get('message', '결제 승인 실패')
        code = res_json.get('code', 'FAIL')
        return redirect(f"{next_url}/payment?code={code}&message={error_msg}")

@payment_bp.route('/toss/fail', methods=['GET'])
def toss_fail():
    """
    토스 결제 실패 리다이렉트 처리
    """
    code = request.args.get('code')
    message = request.args.get('message')

    # 요청 파라미터에서 'next_url' 받아오기
    next_url = request.args.get('next_url')

    # next_url이 없으면 에러 처리 (리다이렉트 불가)
    if not next_url:
        return {'code': 'FAIL', 'message': 'Next URL is missing'}, 400

    return redirect(f"{next_url}/payment?code={code}&message={message}")