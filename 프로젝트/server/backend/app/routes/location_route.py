from flask import Blueprint, jsonify, request
from app.services import location_service
from app.schemas.location_schema import locations_schema, location_schema

location_bp = Blueprint('location', __name__)

@location_bp.route('/', methods=['GET'])
def get_locations():
    """
    위치 정보 조회 (전체 또는 코드별)
    ---
    tags:
      - Location
    parameters:
      - name: location_code
        in: query
        type: string
        description: "위치 코드 (예: PARK-001)"
        required: false
    responses:
      200:
        description: 위치 정보 조회 성공
        schema:
            oneOf:
                - type: array
                  items:
                    $ref: '#/definitions/Location'
                - $ref: '#/definitions/Location'
      404:
        description: 해당 코드의 위치 정보 없음
    """
    code = request.args.get('location_code')
    category = request.args.get('category')
    
    if code:
        location = location_service.get_location_by_code(code)
        if not location:
            return jsonify({"error": "Location not found"}), 404
        return jsonify(location_schema.dump(location))
    
    if category:
        locations = location_service.get_locations_by_category(category)
        return jsonify(locations_schema.dump(locations))
    
    locations = location_service.get_all_locations()
    return jsonify(locations_schema.dump(locations))
