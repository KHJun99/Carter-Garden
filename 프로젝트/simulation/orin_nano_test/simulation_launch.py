import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, RegisterEventHandler, TimerAction, ExecuteProcess
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_xml.launch_description_sources import XMLLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.event_handlers import OnProcessExit
from launch.conditions import IfCondition
from launch.substitutions import Command, LaunchConfiguration

def generate_launch_description():
    current_dir = os.path.dirname(os.path.realpath(__file__))

    # --- [설정] 시작 위치 및 각도 변수화 (여기만 바꾸면 다 적용되도록) ---
    init_x = '1.4'
    init_y = '1.46'
    init_z = '0.01'
    init_yaw = '-1.57'  # y- 방향 (약 -90도)

    # 모델명 설정
    turtlebot_model = os.environ.get('TURTLEBOT3_MODEL', 'waffle_pi')
    print(f"!!! [simulation_launch] Using Model: {turtlebot_model} !!!")

    # 1. 경로 설정
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')
    gazebo_ros_dir = get_package_share_directory('gazebo_ros')
    turtlebot3_gazebo_dir = get_package_share_directory('turtlebot3_gazebo')
    turtlebot3_desc_dir = get_package_share_directory('turtlebot3_description')

    map_file = os.path.join(current_dir, 'worlds', 'mart.yaml')
    world_file = os.path.join(current_dir, 'worlds', 'mart.world')

    # RViz 설정 파일 경로 (Nav2 기본 설정 사용, 필요하면 경로 수정)
    rviz_config_dir = os.path.join(nav2_bringup_dir, 'rviz', 'nav2_default_view.rviz')

    sdf_path = os.path.join(turtlebot3_gazebo_dir, 'models', f'turtlebot3_{turtlebot_model}', 'model.sdf')
    urdf_path = os.path.join(turtlebot3_desc_dir, 'urdf', f'turtlebot3_{turtlebot_model}.urdf')

    # 2. Launch Argument 설정
    use_rviz = LaunchConfiguration('use_rviz')
    declare_use_rviz = DeclareLaunchArgument('use_rviz', default_value='True', description='Start RViz2 automatically')

    # 3. Gazebo 서버 & 클라이언트
    gzserver_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(gazebo_ros_dir, 'launch', 'gzserver.launch.py')),
        launch_arguments={'world': world_file}.items()
    )

    gzclient_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(gazebo_ros_dir, 'launch', 'gzclient.launch.py'))
    )

    # 4. Robot State Publisher (Xacro 변환 적용)
    # xacro 명령어를 통해 ${namespace} 같은 변수를 처리한 뒤 로봇 모델을 불러옵니다.
    robot_desc = Command(['xacro ', urdf_path])

    robot_state_publisher_cmd = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'use_sim_time': True,
            'robot_description': robot_desc
        }]
    )

    # 5. 로봇 스폰 (Spawn Entity)
    spawn_turtlebot_cmd = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-entity', f'turtlebot3_{turtlebot_model}',
            '-file', sdf_path,
            '-x', init_x, '-y', init_y, '-z', init_z,
            '-Y', init_yaw  # [중요] -Y 옵션이 Yaw(회전)입니다. 대문자 Y 주의!
        ],
        output='screen'
    )

    # 6. Nav2 실행 (Bringup) - xterm 분리
    # ExecuteProcess를 사용하여 별도의 터미널 창에서 ros2 launch 실행
    bringup_cmd = ExecuteProcess(
        cmd=[
            'xterm', '-T', 'Nav2_Bringup', '-e',
            'ros2', 'launch', 'nav2_bringup', 'bringup_launch.py',
            f'map:={map_file}',
            'use_sim_time:=True',
            'autostart:=True',
            f'params_file:={os.path.join(nav2_bringup_dir, "params", "nav2_params.yaml")}',
            # f'params_file:={os.path.join(current_dir, "config", "follower_params.yaml")}',
            f'initial_pose_x:={init_x}',
            f'initial_pose_y:={init_y}',
            f'initial_pose_yaw:={init_yaw}'
        ],
        output='screen'
    )

    # 7. RViz 실행 노드 (추가됨!) - xterm 분리
    rviz_cmd = Node(
        condition=IfCondition(use_rviz),
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_dir],
        parameters=[{'use_sim_time': True}],
        output='screen',
        # prefix='xterm -T RViz -e' # 터미널 분리
    )

    # 8. Rosbridge
    rosbridge_dir = get_package_share_directory('rosbridge_server')
    start_rosbridge = IncludeLaunchDescription(
        XMLLaunchDescriptionSource(os.path.join(rosbridge_dir, 'launch', 'rosbridge_websocket_launch.xml'))
    )

    # 9. Web Video Server (MJPEG Streamer)
    # web_video_server 패키지가 설치되어 있어야 합니다. (sudo apt install ros-humble-web-video-server)
    start_web_video_server = Node(
        package='web_video_server',
        executable='web_video_server',
        name='web_video_server',
        output='screen',
        parameters=[{'port': 8080}] # 기본 포트 8080
    )

    # --- [핵심] 실행 순서 제어 (Event Handlers) ---

    # 전략:
    # 1. Gazebo, RobotStatePublisher, Rosbridge는 바로 실행
    # 2. 로봇 스폰(spawn_entity)은 Gazebo 실행과 동시에 시작되지만 내부적으로 서비스 대기함
    # 3. **[중요]** Nav2(bringup_cmd)는 'spawn_entity'가 끝난(Exit) 후에 실행 -> TF 트리 완성 후 Nav2 켜짐
    # 4. RViz는 Nav2가 켜진 후에 실행 (또는 Nav2와 같이)

    bringup_timer = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_turtlebot_cmd,
            on_exit=[bringup_cmd] # 스폰이 끝나면 Nav2 실행
        )
    )

    rviz_timer = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_turtlebot_cmd, # 혹은 bringup_cmd 실행 후 딜레이를 줄 수도 있음
            on_exit=[rviz_cmd] # 스폰 끝나면 RViz도 실행
        )
    )

    ld = LaunchDescription()

    # 기본 선언
    ld.add_action(declare_use_rviz)

    # 즉시 실행할 노드들
    ld.add_action(gzserver_cmd)
    ld.add_action(gzclient_cmd)
    ld.add_action(robot_state_publisher_cmd)
    ld.add_action(start_rosbridge)
    ld.add_action(start_web_video_server)
    ld.add_action(spawn_turtlebot_cmd) # 스폰 시작

    # 순차 실행할 노드들 (핸들러로 묶음)
    ld.add_action(bringup_timer) # 스폰 완료 -> Nav2
    ld.add_action(rviz_timer)    # 스폰 완료 -> RViz

    return ld
