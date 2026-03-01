import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from std_msgs.msg import String
from nav2_msgs.action import NavigateThroughPoses
import yaml
import json

class RobotController(Node):
    def __init__(self):
        super().__init__('robot_master_controller')
        
        # Real robot -> use_sim_time False by default
        # real_controller.py 15번 줄 근처 수정
        try:
            # 파라미터가 이미 있어도 에러 없이 넘어가도록 예외 처리
            self.declare_parameter('use_sim_time', False)
        except Exception:
            pass
        
        self.get_logger().info(">>> Real Robot Master Controller Started")
        
        self.current_mode = "IDLE"
        
        # 1. Nav2 Setup
        self.init_pose_pub = self.create_publisher(PoseWithCovarianceStamped, '/initialpose', 10)
        self.status_pub = self.create_publisher(String, '/robot/status', 10)
        self.nav_client = ActionClient(self, NavigateThroughPoses, 'navigate_through_poses')
        
        # 2. Communication Setup
        self.create_subscription(String, '/robot/destination', self.goal_callback, 10)
        self.create_subscription(String, '/robot/mode', self.mode_callback, 10)
        self.create_subscription(String, '/robot/set_init_pose', self.init_callback, 10)

        # 3. Location Publishing
        self.current_pose_pub = self.create_publisher(String, '/robot/current_pose', 10)
        self.create_subscription(PoseWithCovarianceStamped, '/amcl_pose', self.pose_callback, 10)

        self.goal_handle = None

    # -------------------------------------------------------------------------
    # [Callback] Mode Change (/robot/mode)
    # -------------------------------------------------------------------------
    def mode_callback(self, msg):
        req_mode = msg.data.upper()
        if req_mode == self.current_mode: return
        self.get_logger().info(f"Mode Switch: {self.current_mode} -> {req_mode}")

        if req_mode == "STOP":
            if self.goal_handle:
                self.get_logger().info("Stop Request Received")
                self.goal_handle.cancel_goal_async()
            self.status_pub.publish(String(data="ROBOT_STOPPED"))

        self.current_mode = req_mode
        self.status_pub.publish(String(data=f"ACK_{req_mode}"))

    # -------------------------------------------------------------------------
    # [Callback] Nav2 Destination (/robot/destination)
    # -------------------------------------------------------------------------
    def goal_callback(self, msg):
        # Auto-switch to NAV mode
        self.current_mode = "NAV"
        try:
            self.get_logger().info(f"[DEBUG] Raw Destination Message: {msg.data}")
            payload = yaml.safe_load(msg.data)
            if payload.get('command') != 'navigate_waypoints':
                self.get_logger().warn(f"[DEBUG] Unknown command: {payload.get('command')}")
                return

            waypoints = payload.get('waypoints', [])
            
            print("\n" + "="*50)
            print(f" [Vue Command] Total {len(waypoints)} waypoints")
            for i, wp in enumerate(waypoints):
                print(f"  - WP {i+1}: ({wp['x']}, {wp['y']})")
            print("="*50 + "\n")

            self.send_waypoints(waypoints)
            
        except Exception as e:
            self.get_logger().error(f"Failed to parse command: {e}")

    # -------------------------------------------------------------------------
    # [Callback] Set Initial Pose (/robot/set_init_pose)
    # -------------------------------------------------------------------------
    def init_callback(self, msg):
        try:
            data = yaml.safe_load(msg.data)
            p = PoseWithCovarianceStamped()
            p.header.frame_id = 'map'
            p.header.stamp = self.get_clock().now().to_msg()
            p.pose.pose.position.x = float(data['x'])
            p.pose.pose.position.y = float(data['y'])
            p.pose.pose.orientation.w = 1.0 
            p.pose.covariance = [0.1] * 36
            
            self.init_pose_pub.publish(p)
            self.get_logger().info(f"Initial Pose Set: ({data['x']}, {data['y']})")
        except Exception as e:
            self.get_logger().error(f"Init Pose Error: {e}")

    # -------------------------------------------------------------------------
    # [Callback] Current Robot Pose (AMCL)
    # -------------------------------------------------------------------------
    def pose_callback(self, msg):
        try:
            x = msg.pose.pose.position.x
            y = msg.pose.pose.position.y
            pose_data = json.dumps({'x': x, 'y': y})
            self.current_pose_pub.publish(String(data=pose_data))
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # [Nav2] Send Waypoints
    # -------------------------------------------------------------------------
    def send_waypoints(self, waypoints):
        self.get_logger().info(f"[DEBUG] Waiting for Nav2 Action Server...")
        if not self.nav_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error("[DEBUG] Nav2 Action Server Not Available!")
            return

        self.get_logger().info(f"[DEBUG] Constructing Goal with {len(waypoints)} waypoints")
        goal_msg = NavigateThroughPoses.Goal()
        
        for wp in waypoints:
            pose = PoseStamped()
            pose.header.frame_id = 'map'
            pose.header.stamp = self.get_clock().now().to_msg()
            
            pose.pose.position.x = float(wp['x'])
            pose.pose.position.y = float(wp['y'])
            pose.pose.orientation.z = float(wp['z'])
            pose.pose.orientation.w = float(wp['w'])
            
            goal_msg.poses.append(pose)

        self.get_logger().info(f"Starting Navigation to {len(waypoints)} waypoints")
        future = self.nav_client.send_goal_async(goal_msg)
        future.add_done_callback(self.response_callback)

    def response_callback(self, future):
        self.get_logger().info("[DEBUG] Received Goal Response from Nav2")
        handle = future.result()
        if not handle.accepted:
            self.get_logger().warn("[DEBUG] Nav2 Rejected the Goal!")
            return
        self.goal_handle = handle
        self.get_logger().info("[DEBUG] Goal Accepted. Moving...")
        handle.get_result_async().add_done_callback(self.result_callback)

    def result_callback(self, future):
        status = future.result().status
        self.get_logger().info(f"[DEBUG] Navigation Finished with Status: {status}")
        if status == 4: # SUCCEEDED
            self.get_logger().info("Arrived at Destination!")
            self.status_pub.publish(String(data="ARRIVED"))
        self.goal_handle = None

    def destroy_node(self):
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = RobotController()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
