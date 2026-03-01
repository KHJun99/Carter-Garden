import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from nav2_msgs.action import NavigateThroughPoses
import threading
import sys
import time
import math  # 추가: 거리 계산용

# 사용자 정의 모듈
import graph_data
import path_planner

class PathSmoother:
    @staticmethod
    def smooth_path(waypoints):
        # [TODO] 경로 평활화 로직 (B-Spline 등)
        return waypoints

class SimpleWaypointNavigator(Node):
    def __init__(self):
        super().__init__('simple_waypoint_navigator')
        
        # --- Publishers ---
        self.initial_pose_pub = self.create_publisher(PoseWithCovarianceStamped, '/initialpose', 10)
        
        # --- Subscribers ---
        # [Feedback 반영] 실제 위치 추적을 위한 AMCL Pose 구독
        self.create_subscription(PoseWithCovarianceStamped, '/amcl_pose', self.amcl_pose_callback, 10)
        
        # --- Action Client ---
        self._action_client = ActionClient(self, NavigateThroughPoses, 'navigate_through_poses')
        
        # --- State Variables ---
        self.current_node_id = None  # 논리적 현재 노드
        self.last_goal_node = None   # STOP/RESUME용 마지막 목표 노드
        self.is_navigating = False
        self.goal_handle = None      # 취소(STOP)를 위한 핸들
        self.current_pose = None     # [Feedback 반영] 실시간 물리적 위치
        
        self.get_logger().info("Nav2 Action Server 연결 대기 중...")
        self._action_client.wait_for_server()
        self.get_logger().info("시스템 준비 완료. 'init <NodeID>'로 시작하세요.")

    def amcl_pose_callback(self, msg):
        """ 실시간 로봇 위치 업데이트 """
        self.current_pose = msg.pose.pose

    def find_nearest_node(self):
        """ [Feedback 반영] 현재 위치에서 가장 가까운 그래프 노드 찾기 """
        if not self.current_pose:
            return None
        
        min_dist = float('inf')
        nearest_node = None
        
        rx = self.current_pose.position.x
        ry = self.current_pose.position.y
        
        for node_id, (nx, ny) in graph_data.NODES.items():
            dist = math.hypot(nx - rx, ny - ry)
            if dist < min_dist:
                min_dist = dist
                nearest_node = node_id
                
        return nearest_node

    def set_initial_pose(self, node_id):
        """ 초기 위치 설정 및 상태 업데이트 """
        if node_id not in graph_data.NODES:
            self.get_logger().error(f"존재하지 않는 노드: {node_id}")
            return

        x, y = graph_data.NODES[node_id]
        msg = PoseWithCovarianceStamped()
        msg.header.frame_id = 'map'
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.pose.pose.position.x = x
        msg.pose.pose.position.y = y
        msg.pose.pose.orientation.w = 1.0
        msg.pose.covariance = [0.0] * 36
        msg.pose.covariance[0] = 0.1; msg.pose.covariance[7] = 0.1; msg.pose.covariance[35] = 0.05
        
        self.initial_pose_pub.publish(msg)
        
        # 상태 업데이트
        self.current_node_id = node_id
        self.is_navigating = False
        self.get_logger().info(f"초기 위치 설정 완료: {node_id} ({x}, {y})")

    def stop_navigation(self):
        """ 주행 중단 (STOP) """
        if self.goal_handle and self.is_navigating:
            self.get_logger().info("주행을 정지합니다 (Canceling goal)...")
            self.goal_handle.cancel_goal_async()
            self.is_navigating = False
        else:
            self.get_logger().warn("현재 진행 중인 주행이 없습니다.")

    def resume_navigation(self):
        """ 주행 재개 (RESUME) """
        if not self.last_goal_node:
            self.get_logger().warn("재개할 목표(이전 목적지)가 없습니다.")
            return
        
        # [Feedback 반영] 현재 실제 위치를 기반으로 출발 노드 재설정
        nearest = self.find_nearest_node()
        if nearest:
            self.get_logger().info(f"[RESUME] 현재 위치와 가장 가까운 노드 '{nearest}'에서 경로를 재계산합니다.")
            self.current_node_id = nearest
        else:
            self.get_logger().warn("[RESUME] 현재 위치(AMCL)를 알 수 없습니다. 마지막 기억된 노드에서 시작합니다.")
        
        self.get_logger().info(f"주행 재개: {self.current_node_id} -> {self.last_goal_node}")
        self.execute_navigation(self.last_goal_node)

    def create_pose(self, x, y, orientation):
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.orientation.z = orientation['z']
        pose.pose.orientation.w = orientation['w']
        return pose

    def execute_navigation(self, goal_node):
        """ 목적지 노드로 이동 (현재 노드에서 출발) """
        if not self.current_node_id:
            self.get_logger().error("초기 위치(init)가 설정되지 않았습니다.")
            return
            
        start_node = self.current_node_id
        
        # 1. Dijkstra 경로 탐색
        self.get_logger().info(f"경로 계산: {start_node} -> {goal_node}")
        node_path = path_planner.run_dijkstra(start_node, goal_node)
        
        if not node_path:
            self.get_logger().error(f"[Path Planner] 경로를 찾을 수 없습니다: {start_node} -> {goal_node}")
            return

        print(f" -> 경로: {node_path}")

        # 2. Waypoint 변환 (출발지 제외)
        raw_waypoints = []
        for i in range(1, len(node_path)):
            prev_id = node_path[i-1]
            curr_id = node_path[i]
            
            x, y = graph_data.NODES[curr_id]
            orientation = path_planner.get_target_orientation(prev_id, curr_id)
            
            pose = self.create_pose(x, y, orientation)
            raw_waypoints.append(pose)

        if not raw_waypoints:
            self.get_logger().info("이미 목적지에 있습니다.")
            return

        # 3. Path Smoother
        smoothed_waypoints = PathSmoother.smooth_path(raw_waypoints)

        # 4. Action 전송
        goal_msg = NavigateThroughPoses.Goal()
        goal_msg.poses = smoothed_waypoints
        
        self.get_logger().info(f"Nav2로 이동 명령 전송 ({len(smoothed_waypoints)} steps)...")
        
        self.last_goal_node = goal_node # 재개를 위해 저장
        
        future = self._action_client.send_goal_async(goal_msg)
        future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        self.goal_handle = future.result()
        if not self.goal_handle.accepted:
            self.get_logger().error("Nav2가 요청을 거절했습니다.")
            return

        self.get_logger().info("주행 시작! (Moving...)")
        self.is_navigating = True
        
        get_result_future = self.goal_handle.get_result_async()
        get_result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        status = future.result().status
        self.is_navigating = False
        
        if status == 4: # SUCCEEDED
            self.get_logger().info(f"목적지 {self.last_goal_node} 도착 완료.")
            # 도착했으므로 현재 위치를 목적지로 업데이트
            self.current_node_id = self.last_goal_node
        elif status == 5: # CANCELED
            self.get_logger().warn("주행이 취소되었습니다 (STOP).")
        else:
            self.get_logger().warn(f"주행 비정상 종료 (Status: {status})")

# --- CLI ---
def input_loop(navigator):
    print("\n[Command List]")
    print(" - init <NodeID> : 초기 위치 설정 (예: init P0)")
    print(" - go <GoalID>   : 현재 위치에서 목적지로 이동 (예: go P6)")
    print(" - stop          : 주행 정지")
    print(" - resume        : 주행 재개")
    print(" - q             : 종료")
    
    while rclpy.ok():
        try:
            cmd = input("\nCmd >> ").strip().split()
            if not cmd: continue
            
            op = cmd[0].lower()
            
            if op == 'q':
                print("종료합니다.")
                rclpy.shutdown()
                break
                
            elif op == 'init':
                if len(cmd) < 2: print("Usage: init <NodeID>"); continue
                navigator.set_initial_pose(cmd[1])
                
            elif op == 'go':
                if len(cmd) < 2: print("Usage: go <GoalID>"); continue
                navigator.execute_navigation(cmd[1])
            
            elif op == 'stop':
                navigator.stop_navigation()
                
            elif op == 'resume':
                navigator.resume_navigation()
                
            else:
                print("Unknown command.")
                
        except Exception as e:
            print(f"Error: {e}")

def main():
    rclpy.init()
    navigator = SimpleWaypointNavigator()
    
    t = threading.Thread(target=input_loop, args=(navigator,), daemon=True)
    t.start()
    
    try:
        rclpy.spin(navigator)
    except KeyboardInterrupt:
        pass
    finally:
        navigator.destroy_node()

if __name__ == '__main__':
    main()
