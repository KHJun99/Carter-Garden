from flask import Blueprint, jsonify, request
from app.schemas.product_schema import product_schema, products_schema, categories_schema
from app.services import product_service

product_bp = Blueprint('product', __name__)

# --- 상품 목록 조회 (필터/검색) ---
@product_bp.route('/', methods=['GET'])
def get_products():
    """
    상품 목록 조회 (카테고리 필터 / 검색)
    ---
    tags:
      - Product
    description: 카테고리 별 또는 검색을 통해 필터링 된 상품 목록을 조회합니다.
    parameters:
      - name: category_id
        in: query
        type: integer
        description: "카테고리 ID (필터링)"
        required: false
      - name: keyword
        in: query
        type: string
        description: "검색어 (상품명, 설명)"
        required: false
    responses:
      200:
        description: 상품 목록 조회 성공
        schema:
          type: object
          properties:
            products:
              type: array
              items:
                $ref: '#/definitions/Product'
            count:
              type: integer
    """
    category_id = request.args.get('category_id', type=int)
    keyword = request.args.get('keyword', type=str)

    products, total_count = product_service.get_filtered_products(
        category_id=category_id,
        search_keyword=keyword
    )

    return jsonify({
        "products": products_schema.dump(products),
        "count": total_count
    })

# --- 상품 상세 조회 ---
@product_bp.route('/<int:product_id>', methods=['GET'])
def get_product_byID(product_id):
    """
    상품 상세 정보 조회
    ---
    tags:
      - Product
    description: 상품 id에 해당하는 상품 상세 정보를 반환합니다.
    parameters:
      - name: product_id
        in: path
        type: integer
        required: true
        description: 상품 고유 ID
    responses:
      200:
        description: 조회 성공
        schema:
          $ref: '#/definitions/Product'
      404:
        description: 해당 상품 없음
    """
    product = product_service.get_product_by_id(product_id)
    return jsonify(product_schema.dump(product))

# --- 카테고리 목록 조회 ---
@product_bp.route('/categories', methods=['GET'])
def get_categories():
    """
    전체 카테고리 목록 조회
    ---
    tags:
      - Product
    description: 카테고리 목록을 반환합니다.
    responses:
      200:
        description: 카테고리 목록 반환
        schema:
          type: array
          items:
            type: object
            properties:
              category_id:
                type: integer
              category_name:
                type: string
    """
    categories = product_service.get_all_categories()
    return jsonify(categories_schema.dump(categories))

# --- AI 상품 추천 ---
@product_bp.route('/recommend', methods=['POST'])
def recommend_products():
    """
    AI 상품 추천 (현재 장바구니/보고 있는 상품 제외)
    ---
    tags:
      - Product
    description: AI가 추천한 상품 정보를 반환합니다.
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            cart_id:
              type: integer
              description: 현재 사용 중인 카트 ID
              example: 101
            product_ids:
              type: array
              items:
                type: integer
              description: 현재 장바구니에 담긴(또는 보고 있는) 상품 ID 목록
              example: [1, 5, 12]
    responses:
      200:
        description: 추천 상품 반환 (1개)
        schema:
          $ref: '#/definitions/Product'
      400:
        description: cart_id 누락
      404:
        description: 추천할 상품이 없음
    """
    data = request.json or {}
    cart_id = data.get('cart_id')
    product_ids = data.get('product_ids', [])

    recommendation = product_service.recommend_product_by_ai(product_ids)
    if not recommendation:
        return jsonify({"message": "추천 실패"}), 404

    return jsonify(product_schema.dump(recommendation))
