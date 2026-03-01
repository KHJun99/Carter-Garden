import os
import sys
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, ExecuteProcess, RegisterEventHandler
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_xml.launch_description_sources import XMLLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch.event_handlers import OnProcessExit

def generate_launch_description():
    current_dir = os.path.dirname(os.path.realpath(__file__))

    # 1. Paths & Configurations
    # ---------------------------------------------------------
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')
    turtlebot3_desc_dir = get_package_share_directory('turtlebot3_description')

    # Using 'waffle_pi' or environment variable
    turtlebot_model = os.environ.get('TURTLEBOT3_MODEL', 'waffle_pi')

    # Path to map file (Default: mart.yaml in worlds folder)
    default_map_file = os.path.join(current_dir, 'worlds', 'mart.yaml')

    # URDF path
    urdf_path = os.path.join(turtlebot3_desc_dir, 'urdf', f'turtlebot3_{turtlebot_model}.urdf')

    # Launch Arguments
    map_file = LaunchConfiguration('map')
    declare_map_file = DeclareLaunchArgument(
        'map',
        default_value=default_map_file,
        description='Full path to map file to load'
    )

    # 2. Hardware Drivers
    # ---------------------------------------------------------

    # Lidar Driver (ydlidar_ros2_driver)
    # Assumes 'ydlidar_ros2_driver' package is installed and 'ydlidar_launch.py' exists
    ydlidar_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('ydlidar_ros2_driver'), 'launch', 'ydlidar_launch.py')
        )
    )

    # USB Camera Node (publishing /camera/image_raw)
    # Using 'usb_cam' package. If not installed, this will fail.
    # Alternatively, use v4l2_camera if usb_cam is missing.
    usb_cam_node = Node(
        package='usb_cam',
        executable='usb_cam_node_exe',
        name='usb_cam',
        output='screen',
        parameters=[{
            'video_device': '/dev/video0',
            'framerate': 30.0,
            'image_width': 640,
            'image_height': 480,
            'pixel_format': 'mjpeg2rgb'  # [수정] yuyv -> mjpeg2rgb
        }]
    )

    # IMU Publisher (Standalone Script)
    imu_cmd = ExecuteProcess(
        cmd=[sys.executable, os.path.join(current_dir, '6_imu_publisher.py')],
        output='screen'
    )

    # Odom Publisher (Standalone Script)
    odom_cmd = ExecuteProcess(
        cmd=[sys.executable, os.path.join(current_dir, '5_odom_publisher.py')],
        output='screen'
    )

    # Robot State Publisher
    robot_desc = Command(['xacro ', urdf_path])
    robot_state_publisher_cmd = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'use_sim_time': False,
            'robot_description': robot_desc
        }]
    )

    # 3. Core Systems (Nav2, Communication)
    # ---------------------------------------------------------

    # Nav2 Bringup
    bringup_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_dir, 'launch', 'bringup_launch.py')
        ),
        launch_arguments={
            'map': map_file,
            'use_sim_time': 'False',
            'params_file': os.path.join(nav2_bringup_dir, 'params', 'nav2_params.yaml'),
            #'params_file': os.path.join(current_dir, 'config', 'follower_params.yaml'),
            'autostart': 'True'
        }.items()
    )

    # Rosbridge Server
    rosbridge_launch = IncludeLaunchDescription(
        XMLLaunchDescriptionSource(
            os.path.join(get_package_share_directory('rosbridge_server'), 'launch', 'rosbridge_websocket_launch.xml')
        ),
        launch_arguments={'address': '0.0.0.0'}.items()
    )

    # Web Video Server
    web_video_server_node = Node(
        package='web_video_server',
        executable='web_video_server',
        name='web_video_server',
        output='screen',
        parameters=[{
        'port': 8080,
        'default_stream_type': 'mjpeg'  # compressed 이미지 지원
        }]
    )

    # 4. Application Nodes
    # ---------------------------------------------------------

    # Follower Node (Standalone Script)
    follower_cmd = ExecuteProcess(
        cmd=[
            sys.executable, os.path.join(current_dir, 'follower_node.py'),
            '--ros-args', '-p', 'use_sim_time:=False'
        ],
        output='screen'
    )

    # Real Controller (Standalone Script)
    controller_cmd = ExecuteProcess(
        cmd=[
            sys.executable, os.path.join(current_dir, 'real_controller.py'),
            '--ros-args', '-p', 'use_sim_time:=False'
        ],
        output='screen'
    )

    ld = LaunchDescription()

    # Args
    ld.add_action(declare_map_file)

    # Hardware
    ld.add_action(ydlidar_launch)
    ld.add_action(usb_cam_node)
    ld.add_action(imu_cmd)
    ld.add_action(odom_cmd)
    ld.add_action(robot_state_publisher_cmd)

    # Core & Network
    ld.add_action(rosbridge_launch)
    ld.add_action(web_video_server_node)
    ld.add_action(bringup_cmd)

    # Application
    ld.add_action(follower_cmd)
    ld.add_action(controller_cmd)

    return ld
