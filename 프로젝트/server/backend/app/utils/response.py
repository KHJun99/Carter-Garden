# app/utils/response.py
# Response format utilities
from flask import jsonify

def success_response(data=None, message="Success", status_code=200):
    """
    성공 응답 포맷
    {
        "result": "success",
        "message": "Success",
        "data": { ... }
    }
    """
    response = {
        "result": "success",
        "message": message,
        "data": data if data is not None else {}
    }
    return jsonify(response), status_code

def error_response(message="Error", status_code=400):
    """
    에러 응답 포맷
    {
        "result": "fail",
        "message": "에러 메시지"
    }
    """
    response = {
        "result": "fail",
        "message": message
    }
    return jsonify(response), status_code