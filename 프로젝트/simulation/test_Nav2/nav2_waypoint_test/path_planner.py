import math
import heapq
import graph_data

def get_dist(p1_id, p2_id):
    """ 두 노드 사이의 유클리드 거리 계산 """
    x1, y1 = graph_data.NODES[p1_id]
    x2, y2 = graph_data.NODES[p2_id]
    return math.hypot(x2 - x1, y2 - y1)

def run_dijkstra(start_id, goal_id):
    """ 최단 경로 노드 ID 리스트 반환 """
    # (cost, current_node_id, path_list)
    pq = [(0, start_id, [])]

    # 최단 거리 기록용 (초기화)
    min_costs = {node: float('inf') for node in graph_data.NODES}
    min_costs[start_id] = 0

    while pq:
        cost, cur, path = heapq.heappop(pq)

        # 이미 처리된 더 짧은 경로가 있다면 스킵
        if cost > min_costs[cur]:
            continue

        current_path = path + [cur]

        # 목적지 도착
        if cur == goal_id:
            return current_path

        # 이웃 노드 탐색
        if cur in graph_data.EDGES:
            for neighbor in graph_data.EDGES[cur]:
                new_cost = cost + get_dist(cur, neighbor)

                if new_cost < min_costs[neighbor]:
                    min_costs[neighbor] = new_cost
                    heapq.heappush(pq, (new_cost, neighbor, current_path))
    return None

def get_target_orientation(cur_id, next_id):
    """
    다음 노드로 갈 때 필요한 방향(Quaternion) 반환
    미리 정의된 방향이 있으면 사용
    없으면 좌표 기반 계산
    """
    # 미리 정의된 방향 확인
    if cur_id in graph_data.EDGES and next_id in graph_data.EDGES[cur_id]:
        return graph_data.EDGES[cur_id][next_id]

    # 정의되지 않은 경우 좌표 기반 자동 계산
    print(f"[INFO] 방향 정보 자동 계산: {cur_id} -> {next_id}")
    return calculate_quaternion_from_points(cur_id, next_id)

def calculate_quaternion_from_points(p1_id, p2_id):
    """ 두 노드의 좌표를 바탕으로 진행 방향각도 반각 계산 """
    x1, y1 = graph_data.NODES[p1_id]
    x2, y2 = graph_data.NODES[p2_id]

    yaw = math.atan2(y2 - y1, x2 - x1)

    return {
        'z': math.sin(yaw / 2.0),
        'w': math.cos(yaw / 2.0)
    }
