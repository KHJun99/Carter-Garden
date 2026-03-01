from flask import Blueprint, jsonify
from sqlalchemy import text
from app.extensions import db

map_bp = Blueprint('map', __name__)

@map_bp.route('/', methods=['GET'])
def get_map_graph():
    """
    맵 그래프 데이터 조회 (노드 및 간선)
    ---
    tags:
      - Map
    responses:
      200:
        description: 맵 그래프 데이터 조회 성공
    """
    # 노드 조회
    nodes_query = text("SELECT location_id, location_code, category, pos_x, pos_y FROM locations")
    nodes_result = db.session.execute(nodes_query).fetchall()

    # 간선 조회 (양방향 연결 정보)
    edges_query = text("""
        SELECT
            p.node1_id, l1.location_code as start_code,
            p.node2_id, l2.location_code as end_code
        FROM location_paths p
        JOIN locations l1 ON p.node1_id = l1.location_id
        JOIN locations l2 ON p.node2_id = l2.location_id
    """)
    edges_result = db.session.execute(edges_query).fetchall()

    # 데이터 구조화
    nodes = {
        row.location_code: {
            "id": row.location_id,
            "category": row.category,
            "x": row.pos_x,
            "y": row.pos_y
        } for row in nodes_result
    }

    links = [
        {"from": row.start_code, "to": row.end_code}
        for row in edges_result
    ]

    return jsonify({"nodes": nodes, "links": links})
