# app/routes/s3_route.py
from flask import Blueprint, jsonify

s3_bp = Blueprint('s3', __name__)

@s3_bp.route('/upload', methods=['POST'])
def upload_file():
    return jsonify({"message": "s3 upload endpoint"})
