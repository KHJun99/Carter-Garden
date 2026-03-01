import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import xacro

def generate_launch_description():
    pkg_follower = get_package_share_directory('follower')
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')
    
    # 파일 경로 설정
    map_file = os.path.join(pkg_follower, 'worlds', 'mart.yaml')
    world_file = os.path.join(pkg_follower, 'worlds', 'mart.world')

    # Gazebo, 로봇 소환, Nav2 통합 실행
    start_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(nav2_bringup_dir, 'launch', 'tb3_simulation_launch.py')),
        launch_arguments={
            'map': map_file,
            'world': world_file,
            'use_rviz': 'True',
            'use_simulator': 'True',
            'x_pose': '0.0',
            'y_pose': '0.0',
            'z_pose': '0.01'
        }.items()
    )

    return LaunchDescription([start_sim])
