#!/usr/bin/env python3
# 1.5_keyboard_slam_drive.py - 키보드 주행 + 실시간 SLAM 맵핑 (IMU+Odom 보정 포함)
import sys
import tty
import termios
import threading
import time
import math
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
from sensor_msgs.msg import LaserScan, Imu
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist
import numpy as np
import matplotlib.pyplot as plt
import os
from config import SPEED_NORMAL
from motor_hat import MotorDriverHat


def quaternion_to_yaw(q):
    # q: geometry_msgs/Quaternion-like (x,y,z,w)
    x, y, z, w = q
    # yaw (z) calculation
    t3 = 2.0 * (w * z + x * y)
    t4 = 1.0 - 2.0 * (y * y + z * z)
    return math.atan2(t3, t4)


def normalize_angle(angle):
    while angle > math.pi:
        angle -= 2.0 * math.pi
    while angle < -math.pi:
        angle += 2.0 * math.pi
    return angle


class KeyboardSlamNode(Node):
    def __init__(self):
        super().__init__('keyboard_slam_drive')
        self.scan_data = []  # raw per-scan (angles, ranges)
        self.scan_data_global = []  # per-scan arrays in world frame (x,y)
        self.running = True
        # publish cmd_vel for motor_subscriber to consume
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.map_count = 0

        # robot pose (from odom) and imu yaw override
        self.pose_x = 0.0
        self.pose_y = 0.0
        self.pose_yaw = 0.0
        self.yaw_imu = None
        self.last_imu_time = None

        # QoS for lidar
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )

        # subscribers
        self.create_subscription(LaserScan, '/scan', self.lidar_callback, qos_profile)
        # allow override via parameters
        self.declare_parameter('odom_topic', '/odom')
        self.declare_parameter('imu_topic', '/imu/data')
        odom_topic = self.get_parameter('odom_topic').value
        imu_topic = self.get_parameter('imu_topic').value
        self.create_subscription(Odometry, odom_topic, self.odom_callback, 10)
        self.create_subscription(Imu, imu_topic, self.imu_callback, 50)

        # status timer
        self.create_timer(1.0, self.timer_callback)

        # MotorDriver는 이 노드에서 직접 제어하지 않습니다.
        # 실제 모터 제어는 `motor_subscriber.py`가 `/cmd_vel`을 받아 처리합니다.

    def lidar_callback(self, msg: LaserScan):
        # build angles array matching ranges length
        ranges = np.array(msg.ranges)
        count = len(ranges)
        angles = msg.angle_min + np.arange(count) * msg.angle_increment

        # valid
        valid_mask = (ranges > 0.1) & (ranges < 10.0) & np.isfinite(ranges)
        if not np.any(valid_mask):
            return

        filtered_ranges = ranges[valid_mask]
        filtered_angles = angles[valid_mask]

        # local coordinates
        x_local = filtered_ranges * np.cos(filtered_angles)
        y_local = filtered_ranges * np.sin(filtered_angles)

        # select yaw: prefer IMU yaw (absolute), else odom yaw
        yaw = self.yaw_imu if self.yaw_imu is not None else self.pose_yaw
        c = math.cos(yaw)
        s = math.sin(yaw)

        # transform to world
        x_world = c * x_local - s * y_local + self.pose_x
        y_world = s * x_local + c * y_local + self.pose_y

        # store
        self.scan_data.append((filtered_angles, filtered_ranges))
        self.scan_data_global.append((x_world, y_world))

        if len(self.scan_data_global) % 50 == 0:
            self.get_logger().info(f'📍 맵핑 진행: {len(self.scan_data_global)} 프레임 (global)')

    def odom_callback(self, msg: Odometry):
        p = msg.pose.pose.position
        q = msg.pose.pose.orientation
        self.pose_x = p.x
        self.pose_y = p.y
        # convert quaternion to yaw
        self.pose_yaw = quaternion_to_yaw((q.x, q.y, q.z, q.w))

    def imu_callback(self, msg: Imu):
        # if IMU provides orientation, use it. otherwise integrate gyro z (timestamp-based)
        q = msg.orientation
        has_orientation = any([abs(q.x) > 1e-6, abs(q.y) > 1e-6, abs(q.z) > 1e-6, abs(q.w) > 1e-6])
        if has_orientation:
            self.yaw_imu = quaternion_to_yaw((q.x, q.y, q.z, q.w))
            # reset integration when absolute orientation available
            self.last_imu_time = None
            return

        # integrate gyro z using imu header timestamp
        stamp = msg.header.stamp
        now = stamp.sec + stamp.nanosec * 1e-9
        gz = msg.angular_velocity.z

        if self.last_imu_time is None:
            # initialize integration state
            self.last_imu_time = now
            if self.yaw_imu is None:
                self.yaw_imu = self.pose_yaw
            return

        dt = now - self.last_imu_time
        self.last_imu_time = now
        if 0 < dt < 1.0:
            self.yaw_imu = normalize_angle(self.yaw_imu + gz * dt)

    def timer_callback(self):
        if self.running and (len(self.scan_data_global) > 0) and (len(self.scan_data_global) % 10 == 0):
            self.get_logger().info(f'📊 수집된 스캔: {len(self.scan_data_global)} frames')

    def save_map(self, filename='slam_map.png'):
        if len(self.scan_data_global) == 0:
            print('⚠️  수집된 전역 데이터가 없습니다. 먼저 주행하세요.')
            return

        # cartesian plot
        plt.figure(figsize=(10, 8))
        for x_arr, y_arr in self.scan_data_global:
            plt.plot(x_arr, y_arr, 'b.', markersize=0.5, alpha=0.3)
        plt.axis('equal')
        plt.xlabel('X (m)')
        plt.ylabel('Y (m)')
        plt.title(f'SLAM Map ({len(self.scan_data_global)} frames)')
        plt.grid(True)
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f'✅ {filename} 저장 완료!')
        plt.close()

        # save global points
        all_x = []
        all_y = []
        for x_arr, y_arr in self.scan_data_global:
            all_x.append(x_arr)
            all_y.append(y_arr)

        if len(all_x) > 0:
            x_concat = np.concatenate(all_x)
            y_concat = np.concatenate(all_y)
            npz_name = f'slam_points_global_{self.map_count}.npz'
            np.savez(npz_name, x=x_concat, y=y_concat)
            print(f'✅ 전역 포인트 저장: {npz_name}')

        self.map_count += 1

    def getch(self):
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    def keyboard_thread(self):
        print('\n========================================')
        print('🚗 키보드 SLAM 주행 시작')
        print('----------------------------------------')
        print(' [W] 전진   | [X] 후진')
        print(' [A] 좌회전 | [D] 우회전')
        print(' [S/SPACE] 정지')
        print(' [C] 현재까지의 맵 저장')
        print(' [Q] 종료')
        print('========================================\n')

        try:
            while self.running:
                key = self.getch()
                if key == 'w':
                    self.get_logger().info('🚗 전진 (Forward)')
                    t = Twist(); t.linear.x = SPEED_NORMAL; t.angular.z = 0.0
                    self.cmd_pub.publish(t)
                elif key == 'x':
                    self.get_logger().info('🔙 후진 (Backward)')
                    t = Twist(); t.linear.x = -SPEED_NORMAL; t.angular.z = 0.0
                    self.cmd_pub.publish(t)
                elif key == 'a':
                    self.get_logger().info('↰ 좌회전 (Left)')
                    t = Twist(); t.linear.x = 0.0; t.angular.z = SPEED_NORMAL
                    self.cmd_pub.publish(t)
                elif key == 'd':
                    self.get_logger().info('↱ 우회전 (Right)')
                    t = Twist(); t.linear.x = 0.0; t.angular.z = -SPEED_NORMAL
                    self.cmd_pub.publish(t)
                elif key == 's' or key == ' ':
                    self.get_logger().info('⏸️ 정지 (Stop)')
                    t = Twist(); t.linear.x = 0.0; t.angular.z = 0.0
                    self.cmd_pub.publish(t)
                elif key == 'c':
                    filename = f'slam_map_{self.map_count}.png'
                    self.save_map(filename)
                elif key == 'q':
                    self.get_logger().info('\n⏹️ 종료 중...')
                    # 안전 정지 publish
                    t = Twist(); t.linear.x = 0.0; t.angular.z = 0.0
                    self.cmd_pub.publish(t)
                    self.running = False
                    break
        except Exception as e:
            self.get_logger().error(f'키 입력 오류: {e}')
        except KeyboardInterrupt:
            self.running = False
            self.motor_hat.stop()

    def run(self):
        kb_thread = threading.Thread(target=self.keyboard_thread, daemon=True)
        kb_thread.start()
        try:
            while self.running:
                rclpy.spin_once(self, timeout_sec=0.1)
        except KeyboardInterrupt:
            pass
        finally:
            if self.motor_hat:
                self.motor_hat.stop()
            print('\n✅ 안전 정지 완료')


def main():
    rclpy.init()
    node = KeyboardSlamNode()
    try:
        node.run()
    except Exception as e:
        print(f'❌ 에러: {e}')
    finally:
        node.destroy_node()
        try:
            rclpy.shutdown()
        except:
            pass


if __name__ == '__main__':
    main()
