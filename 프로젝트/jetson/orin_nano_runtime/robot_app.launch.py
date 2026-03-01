import os
import sys
from launch import LaunchDescription
from launch.actions import ExecuteProcess

def generate_launch_description():
    current_dir = os.path.dirname(os.path.realpath(__file__))

    # 1. Follower Node
    follower_cmd = ExecuteProcess(
        cmd=[sys.executable, os.path.join(current_dir, 'follower_node.py'), '--ros-args', '-p', 'use_sim_time:=False'],
        output='screen'
    )

    # 2. Real Controller
    controller_cmd = ExecuteProcess(
        cmd=[sys.executable, os.path.join(current_dir, 'real_controller.py'), '--ros-args', '-p', 'use_sim_time:=False'],
        output='screen'
    )

    # 3. [추가] Motor Subscriber (실제 모터 구동 '다리' 역할)
    motor_cmd = ExecuteProcess(
        cmd=[sys.executable, os.path.join(current_dir, 'sub_motor_control.py'), '--ros-args', '-p', 'use_sim_time:=False'],
        output='screen'
    )

    return LaunchDescription([follower_cmd, controller_cmd, motor_cmd])