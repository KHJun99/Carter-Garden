"""
🗺️ robot_nav_update.launch.py
===========================================
네비게이션 구성 (맵 방식 선택 옵션)

실행: ros2 launch ./robot_nav_update.launch.py [options]

옵션:
  map_type:=existing/slam  맵 방식 선택
    - existing: 기존 맵 파일 사용 (worlds/mart.yaml) [기본값]
    - slam:     SLAM으로 실시간 맵 생성

예시:
  ros2 launch ./robot_nav_update.launch.py                    # 기존 맵 사용
  ros2 launch ./robot_nav_update.launch.py map_type:=slam     # SLAM으로 맵 생성
===========================================
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, ExecuteProcess
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node

def generate_launch_description():
    map_type = LaunchConfiguration('map_type', default='existing')

    current_dir = os.path.dirname(os.path.realpath(__file__))
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')
    
    # 맵 파일 경로 (mart.yaml)
    map_file = os.path.join(current_dir, 'worlds', 'mart.yaml')

    # [추가됨] 🔧 base_footprint ↔ base_link 연결 (중요!)
    tf_footprint_node = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='static_tf_pub_footprint',
        arguments=['0', '0', '0', '0', '0', '0', 'base_link', 'base_footprint'],
        output='screen'
    )

    # 1. 기존 맵 로드 (Nav2 Bringup)
    nav2_bringup_existing = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(nav2_bringup_dir, 'launch', 'bringup_launch.py')),
        launch_arguments={
            'map': map_file,
            'use_sim_time': 'False',
            'params_file': os.path.join(nav2_bringup_dir, 'params', 'nav2_params.yaml'),
            'autostart': 'True'
        }.items(),
        condition=IfCondition(PythonExpression(["'", map_type, "' == 'existing'"]))
    )

    # 2. SLAM 모드 (Online Async)
    slam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('slam_toolbox'), 'launch', 'online_async_launch.py')
        ),
        condition=IfCondition(PythonExpression(["'", map_type, "' == 'slam'"]))
    )

    # 3. Rosbridge (웹 통신)
    rosbridge_node = ExecuteProcess(
        cmd=['ros2', 'run', 'rosbridge_server', 'rosbridge_websocket'],
        output='screen'
    )

    return LaunchDescription([
        tf_footprint_node,      # ← 추가됨!
        nav2_bringup_existing,
        slam_launch,
        rosbridge_node
    ])
