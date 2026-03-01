from flask import Blueprint, jsonify, request
from app.services import park_service
from app.schemas.park_info_schema import park_infos_schema

park_bp = Blueprint('parking', __name__)

@park_bp.route('/search', methods=['GET'])
def search_parking():
    """
    차량 번호 검색 (주차 위치 조회)
    ---
    tags:
      - Parking
    parameters:
      - name: car_number
        in: query
        type: string
        required: true
        description: "차량 번호 (뒷 4자리 권장)"
    responses:
      200:
        description: 검색된 차량 및 주차 위치 목록
        schema:
          type: array
          items:
            $ref: '#/definitions/ParkInfo'
    """
    car_number = request.args.get('car_number')
    if not car_number:
        return jsonify([])

    cars = park_service.search_cars_by_number(car_number)
    return jsonify(park_infos_schema.dump(cars))
