#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from motor_hat import MotorDriverHat
from config import MOTOR_SAFE_SPEED
import time

class MotorSubscriber(Node):
    def __init__(self):
        super().__init__('motor_subscriber')
        self.declare_parameter('cmd_topic', '/cmd_vel')
        self.cmd_topic = self.get_parameter('cmd_topic').value
        self.sub = self.create_subscription(Twist, self.cmd_topic, self.cmd_callback, 10)
        try:
            self.motor = MotorDriverHat()
            self.get_logger().info('✅ MotorDriverHat initialized')
        except Exception as e:
            self.get_logger().error(f'❌ Motor init failed: {e}')
            raise
        self.last_cmd_time = time.time()
        self.cmd_timeout = 0.5
        self.create_timer(0.1, self.watchdog)

    def cmd_callback(self, msg: Twist):
        linear = msg.linear.x
        angular = msg.angular.z

        # simple differential mapping
        # left = linear - angular, right = linear + angular
        left = linear - angular
        right = linear + angular

        # clamp to safe motor limits
        left = max(-MOTOR_SAFE_SPEED, min(MOTOR_SAFE_SPEED, left))
        right = max(-MOTOR_SAFE_SPEED, min(MOTOR_SAFE_SPEED, right))

        # Drive motors (MotorDriverHat.drive expects left, right values)
        self.motor.drive(left, right)
        self.last_cmd_time = time.time()

    def watchdog(self):
        # stop motors if no cmd for timeout seconds
        if (time.time() - self.last_cmd_time) > self.cmd_timeout:
            self.motor.stop()


def main(args=None):
    rclpy.init(args=args)
    node = MotorSubscriber()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.motor.stop()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
