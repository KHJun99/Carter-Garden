import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch.conditions import IfCondition
from launch_ros.actions import Node

def generate_launch_description():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')
    
    # 1. 실행 시 옵션 선택 (기존 맵 사용 혹은 SLAM 모드)
    map_type_arg = DeclareLaunchArgument(
        'map_type', default_value='existing',
        description='Choose: "existing" (mart.yaml) or "slam" (New Map)'
    )
    map_type = LaunchConfiguration('map_type')
    map_file = os.path.join(current_dir, 'worlds', 'mart.yaml')

    # [추가됨] 🔧 base_footprint ↔ base_link 연결 (중요!)
    tf_footprint_node = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='static_tf_pub_footprint',
        arguments=['0', '0', '0', '0', '0', '0', 'base_link', 'base_footprint'],
        output='screen'
    )

    # 2. [existing 모드] 기존 지도(mart.yaml) 로드 및 주행
    nav_existing = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(nav2_bringup_dir, 'launch', 'bringup_launch.py')),
        launch_arguments={
            'map': map_file, 
            'use_sim_time': 'False', 
            'params_file': os.path.join(current_dir, 'config', 'nav2_params.yaml'),
            'autostart': 'True', 
            'slam': 'False'
        }.items(),
        condition=IfCondition(PythonExpression(["'", map_type, "' == 'existing'"]))
    )

    # 3. [slam 모드] 실시간 지도 제작 및 주행
    nav_slam = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(nav2_bringup_dir, 'launch', 'bringup_launch.py')),
        launch_arguments={
            'map': map_file,
            'use_sim_time': 'False', 
            'params_file': os.path.join(current_dir, 'config', 'nav2_params.yaml'),
            'autostart': 'True', 
            'slam': 'True'
        }.items(),
        condition=IfCondition(PythonExpression(["'", map_type, "' == 'slam'"]))
    )

    # 4. Rosbridge (웹 통신)
    rosbridge_node = Node(
        package='rosbridge_server',
        executable='rosbridge_websocket',
        output='screen'
    )

    # 5. Web Video Server (카메라 화면 송출)
    web_video_server_node = Node(
        package='web_video_server', 
        executable='web_video_server',
        parameters=[{'port': 8080}]
    )

    return LaunchDescription([
        map_type_arg, 
        tf_footprint_node,      # ← 추가됨!
        nav_existing, 
        nav_slam, 
        rosbridge_node, 
        web_video_server_node
    ])
