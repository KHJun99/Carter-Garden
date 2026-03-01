import requests
import random
from flask import current_app
from sqlalchemy import or_
from app.models.product import Product, Category
from sqlalchemy.sql.expression import func

def get_filtered_products(category_id=None, search_keyword=None):
    query = Product.query
    
    if search_keyword:
        search_filter = or_(
            Product.product_name.ilike(f"%{search_keyword}%"),
            Product.description.ilike(f"%{search_keyword}%")
        )
        query = query.filter(search_filter)
        
    elif category_id and category_id != 0:
        query = query.filter(Product.category_id == category_id)
    
    products = query.order_by(Product.product_id.asc()).all()
    
    return products, len(products)
# 상품 상세 조회
def get_product_by_id(product_id):
    return Product.query.get_or_404(product_id)

# 카테고리 조회
def get_all_categories():
    return Category.query.all()

# AI기반 상품 추천
def recommend_product_by_ai(current_product_ids):

    # 장바구니 상품 전체 조회
    if not current_product_ids:
        return _get_random_candidates_and_ask_ai([], "General Recommendation")

    # 전체 장바구니 객체 가져오기
    all_cart_products = Product.query.filter(Product.product_id.in_(current_product_ids)).all()

    if not all_cart_products:
        return _get_random_candidates_and_ask_ai([], "General Recommendation")

    # 카테고리 하나 랜덤 선택
    distinct_category_ids = list(set([p.category_id for p in all_cart_products]))
    target_cat_id = random.choice(distinct_category_ids)

    # 카테고리 이름 조회
    target_category = Category.query.get(target_cat_id)
    target_cat_name = target_category.category_name if target_category else "Selected Category"

    # 해당 카테고리에 해당하는 장바구니 상품만 골라내기
    target_cart_products = [p for p in all_cart_products if p.category_id == target_cat_id]

    # AI에게 보낼 이름 리스트 생성
    target_cart_names = [p.product_name for p in target_cart_products]

    # 해당 카테고리 내에서 '후보군' 추출
    candidates = Product.query.filter(
        Product.category_id == target_cat_id,           # 같은 카테고리
        Product.product_id.notin_(current_product_ids)  # 이미 담은 건 제외
    ).order_by(func.random()).limit(30).all()

    # 후보군이 너무 없으면 전체 랜덤 선택
    if len(candidates) < 1:
        print("추천할 상품이 없습니다.")
        return _get_random_candidates_and_ask_ai([p.product_name for p in all_cart_products], "General")

    # AI에게 요청
    return _ask_ai_for_recommendation(target_cart_names, candidates, target_cat_name)

# AI 요청 함수
def _ask_ai_for_recommendation(cart_names, candidates, category_context):

    candidate_map = {p.product_name: p for p in candidates}
    candidates_str = ", ".join(candidate_map.keys())

    # 필터링된 상품들만
    cart_str = ", ".join(cart_names) if cart_names else "Nothing"

    # 설정 로드
    api_url = current_app.config.get('GMS_API_URL')
    api_key = current_app.config.get('GMS_API_KEY')
    model_name = current_app.config.get('GMS_MODEL')

    if not api_key:
        return candidates[0]

    # 나중에 프롬프트 수정해야함.
    category_logic = {
        '식품': "Focus on similar flavors, complementary dishes (e.g., Ramen -> Kimchi), or repurchasing necessities.",
        '생활용품': "Focus on refill usage, brand loyalty, or complementary household needs.",
        '문구완구': "Focus on character affinity, series collection, or age-appropriate utility.",
        '패션': "Focus on style matching (color, material), seasonal relevance, or completing an outfit.",
        '디지털': "Focus on compatibility (specs), accessories for owned devices, or performance upgrades."
    }

    current_logic = category_logic.get(category_context, "Focus on user preferences and high relevance.")

    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert AI Merchandiser. "
                "Your goal is to analyze the user's taste based on their purchase history "
                "and recommend the single best item from the candidate list that maximizes satisfaction."
            )
        },
        {
            "role": "user",
            "content": f"""
            [Context]
            Category: {category_context}
            Recommendation Logic: {current_logic}

            [User's Purchase History]
            The user has previously bought and liked these items:
            {cart_str}

            [Candidate Products]
            You MUST choose ONE item from this list ONLY:
            {candidates_str}

            [Instruction]
            1. Analyze the 'keywords', 'style', and 'purpose' of the items in the Purchase History.
            2. Select ONE item from the Candidate Products that best matches the user's identified taste.
            3. Do NOT explain your reasoning.
            4. Do NOT add any introductory text (e.g., "I recommend...").
            5. Output the exact product name as it appears in the list.

            Output:
            """
        }
    ]

    try:
        headers = { "Authorization": f"Bearer {api_key}", "Content-Type": "application/json" }
        payload = {
            "model": model_name,
            "messages": messages,
            "max_completion_tokens": 50,
            "temperature": 0.3
        }

        response = requests.post(api_url, headers=headers, json=payload, timeout=5)
        response.raise_for_status()

        # AI 추천 상품명
        ai_picked_name = response.json()['choices'][0]['message']['content'].strip()

        if ai_picked_name in candidate_map:
            return candidate_map[ai_picked_name]

        found = Product.query.filter(Product.product_name.ilike(f"%{ai_picked_name}%")).first()
        return found if found else candidates[0]

    except Exception as e:
        print(f"GMS API Error: {e}")
        return candidates[0]

# 전체 랜덤 (Fallback)
def _get_random_candidates_and_ask_ai(cart_names, context_name):
    candidates = Product.query.order_by(func.random()).limit(30).all()
    if not candidates: return None
    return _ask_ai_for_recommendation(cart_names, candidates, context_name)