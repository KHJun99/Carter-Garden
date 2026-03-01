import requests
import base64
from flask import current_app

def confirm_payment(payment_key, order_id, amount):
    """
    토스페이먼츠 승인 요청
    """
    secret_key = current_app.config.get('TOSS_SECRET_KEY')
    if not secret_key:
        print("CRITICAL: TOSS_SECRET_KEY가 설정되지 않았습니다.")
        return {"message": "서버 설정 오류", "code": "CONFIG_ERROR"}, 500

    # Basic Auth 헤더 생성
    secret_key_str = f"{secret_key}:"
    encoded_key = base64.b64encode(secret_key_str.encode("utf-8")).decode("utf-8")
    
    headers = {
        "Authorization": f"Basic {encoded_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "paymentKey": payment_key,
        "orderId": order_id,
        "amount": int(amount)
    }

    url = "https://api.tosspayments.com/v1/payments/confirm"
    
    try:
        res = requests.post(url, headers=headers, json=data, timeout=10)
        res_json = res.json()

        if res.status_code == 200:
            return res_json, 200
        else:
            # 토스에서 내려준 구체적인 에러 로그 기록
            print(f"Toss API Error (Status {res.status_code}): {res_json}")
            return res_json, res.status_code

    except requests.exceptions.Timeout:
        print("Toss API Error: Request Timeout")
        return {"message": "결제 승인 시간 초과", "code": "TIMEOUT"}, 504
    except requests.exceptions.RequestException as e:
        print(f"Toss API Error: {str(e)}")
        return {"message": "네트워크 통신 오류", "code": "NETWORK_ERROR"}, 500