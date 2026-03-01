import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_xml.launch_description_sources import XMLLaunchDescriptionSource  # [수정] XML 로더 추가
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    current_dir = os.path.dirname(os.path.realpath(__file__))

    map_file = os.path.join(current_dir, 'test_map.yaml')
    world_file = os.path.join(current_dir, 'test_map.world')

    nav2_bringup_dir = get_package_share_directory('nav2_bringup')
    launch_dir = os.path.join(nav2_bringup_dir, 'launch')

    use_rviz = LaunchConfiguration('use_rviz')
    headless = LaunchConfiguration('headless')

    declare_use_rviz = DeclareLaunchArgument(
        'use_rviz', default_value='True', description='Whether to start RVIZ')

    declare_headless = DeclareLaunchArgument(
        'headless', default_value='False', description='Whether to execute gzclient')

    # 1. Gazebo & Nav2 실행
    start_tb3_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(launch_dir, 'tb3_simulation_launch.py')),
        launch_arguments={
            'map': map_file,
            'world': world_file,
            'use_rviz': use_rviz,
            'headless': headless,
            'use_simulator': 'True',
            'x_pose': '-5.0',
            'y_pose': '5.0',
            'z_pose': '0.01'
        }.items()
    )

    # 2. Rosbridge Server 실행 (Vue.js 통신용)
    try:
        rosbridge_dir = get_package_share_directory('rosbridge_server')
        # [수정] XML 파일은 XMLLaunchDescriptionSource로 읽어야 함 (기존 PythonSource 에러 수정)
        start_rosbridge = IncludeLaunchDescription(
            XMLLaunchDescriptionSource(os.path.join(rosbridge_dir, 'launch', 'rosbridge_websocket_launch.xml'))
        )
        return LaunchDescription([
            declare_use_rviz,
            declare_headless,
            start_tb3_sim,
            start_rosbridge
        ])
    except Exception as e:
        print(f"!! 경고: rosbridge_server 실행 불가 ({e}). 'sudo apt install ros-humble-rosbridge-suite' 확인 필요.")
        return LaunchDescription([
            declare_use_rviz,
            declare_headless,
            start_tb3_sim
        ])
