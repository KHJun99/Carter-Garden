import os
import sys
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import Command

def generate_launch_description():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    turtlebot3_desc_dir = get_package_share_directory('turtlebot3_description')
    turtlebot_model = os.environ.get('TURTLEBOT3_MODEL', 'waffle_pi')
    urdf_path = os.path.join(turtlebot3_desc_dir, 'urdf', f'turtlebot3_{turtlebot_model}.urdf')

    # [삭제됨] 1. LiDAR (이미 2번 태스크로 실행 중)
    # [삭제됨] 2. TF Publisher (이미 4번 태스크로 실행 중)
    # [삭제됨] 4. IMU & Odom (이미 1, 3번 태스크로 실행 중)

    # =========================================================
    # [남겨야 할 것] 아직 실행 안 된 나머지들
    # =========================================================

    # 1. Camera (이건 아직 안 켰으니까 실행!)
    usb_cam_node = Node(
        package='usb_cam', executable='usb_cam_node_exe', name='usb_cam',
        output='screen',
        parameters=[{'video_device': '/dev/video0', 'framerate': 30.0, 'pixel_format': 'mjpeg2rgb',
        'brightness': 128,             # [수정] 기본값인 128로 복구 (현재 50은 너무 낮음)
        'extra_capabilities': {
        'auto_exposure': 3,        # 자동 노출 모드 유지
        'exposure_dynamic_framerate': True, # 조도에 따라 프레임 유연하게 조절
        'backlight_compensation': 1 # 역광 보정 활성화
    }}]
    )

    # 2. Robot State Publisher (URDF 모델 - 네비게이션 필수)
    robot_desc = Command(['xacro ', urdf_path])
    robot_state_publisher_cmd = Node(
        package='robot_state_publisher', executable='robot_state_publisher',
        parameters=[{'use_sim_time': False, 'robot_description': robot_desc}]
    )

    return LaunchDescription([
        usb_cam_node,
        robot_state_publisher_cmd
    ])