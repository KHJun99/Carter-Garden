import numpy as np
from PIL import Image
import yaml
import os

def create_test_map():
    # ---------------------------------------------------------
    # 1. 공통 설정 (좌표 및 크기)
    # ---------------------------------------------------------
    resolution = 0.05
    min_x, max_x = -10.0, 15.0
    min_y, max_y = -10.0, 30.0

    width_m = max_x - min_x
    height_m = max_y - min_y

    width_px = int(width_m / resolution)
    height_px = int(height_m / resolution)

    print(f"맵 크기: {width_m}m x {height_m}m ({width_px}x{height_px} px)")

    # ---------------------------------------------------------
    # 2. Nav2용 PGM 맵 데이터 생성 (2D Grid)
    # ---------------------------------------------------------
    # 254: Free space (흰색)
    map_data = np.full((height_px, width_px), 254, dtype=np.uint8)

    def to_px(x, y):
        px = int((x - min_x) / resolution)
        py = int((y - min_y) / resolution)
        return px, py

    world_obstacles = []

    # (A) 외곽 벽
    wall_thickness_px = 5
    map_data[0:wall_thickness_px, :] = 0
    map_data[-wall_thickness_px:, :] = 0
    map_data[:, 0:wall_thickness_px] = 0
    map_data[:, -wall_thickness_px:] = 0

    # Gazebo World 데이터 (중심 좌표, 크기)
    # 상단
    world_obstacles.append(((min_x + max_x)/2, max_y, width_m, 0.2))
    # 하단
    world_obstacles.append(((min_x + max_x)/2, min_y, width_m, 0.2))
    # 좌측
    world_obstacles.append((min_x, (min_y + max_y)/2, 0.2, height_m))
    # 우측
    world_obstacles.append((max_x, (min_y + max_y)/2, 0.2, height_m))

    # (B) 매장 중앙 장애물
    shelves = [
        {'x_s': -3.5, 'x_e': -1.5, 'y_s': 13.0, 'y_e': 22.0},
        {'x_s': 1.5, 'x_e': 3.5, 'y_s': 13.0, 'y_e': 22.0}
    ]
    for obs in shelves:
        px_s, py_s = to_px(obs['x_s'], obs['y_s'])
        px_e, py_e = to_px(obs['x_e'], obs['y_e'])
        map_data[py_s:py_e, px_s:px_e] = 0

        w = obs['x_e'] - obs['x_s']
        h = obs['y_e'] - obs['y_s']
        cx = obs['x_s'] + w/2
        cy = obs['y_s'] + h/2
        world_obstacles.append((cx, cy, w, h))

    # (C) 주차장 구분 벽
    sep_wall = {'x_s': -3.0, 'x_e': 15.0, 'y_s': -0.1, 'y_e': 0.1}
    sx_s, sy_s = to_px(sep_wall['x_s'], sep_wall['y_s'])
    sx_e, sy_e = to_px(sep_wall['x_e'], sep_wall['y_e'])
    if sy_s == sy_e: sy_e += 1
    if sx_s == sx_e: sx_e += 1
    map_data[sy_s:sy_e, sx_s:sx_e] = 0

    sw_w = sep_wall['x_e'] - sep_wall['x_s']
    sw_h = 0.2
    sw_cx = sep_wall['x_s'] + sw_w/2
    sw_cy = 0.0
    world_obstacles.append((sw_cx, sw_cy, sw_w, sw_h))

    # (C-2) [NEW] AMCL 위치 추정용 기둥 (Feature Pillars) - Dense Mode
    # LiDAR 인식 범위가 좁아 -10 ~ 10 구간에 집중 배치
    # 사분면별 2~3개 추가 (DB 노드 및 시작점 -5,5 회피)
    pillars = [
        # 1사분면 (+x, +y)
        (4.0, 3.0), (7.0, 6.0), (2.0, 8.0),
        
        # 2사분면 (-x, +y)
        (-3.0, 3.0), (-8.0, 6.0), (-2.0, 7.0),
        # (-5, 5)는 시작점이므로 제외
        
        # 3사분면 (-x, -y)
        (-4.0, -3.0), (-7.0, -6.0), (-2.0, -8.0),

        # 4사분면 (+x, -y)
        (4.0, -3.0), (7.0, -5.0), (2.0, -7.0),

        # 외곽 및 기타 구역 (기존 유지)
        (10.0, 20.0), (-8.0, 20.0)
    ]
    pillar_size = 0.6 # 60cm 기둥

    for px, py in pillars:
        # 맵 데이터 업데이트 (검은색 장애물)
        px_s, py_s = to_px(px - pillar_size/2, py - pillar_size/2)
        px_e, py_e = to_px(px + pillar_size/2, py + pillar_size/2)
        map_data[py_s:py_e, px_s:px_e] = 0
        
        # 월드 장애물 리스트 추가
        world_obstacles.append((px, py, pillar_size, pillar_size))

    # (D) DB 노드 위치 보호
    nodes = [
        (0.0, 10.0), (-6.0, 10.0), (0.0, 10.0), (-6.0, 17.5), (6.0, 17.5), (-2.0, 25.0), (2.0, 25.0),
        (-5.0, 0.0), (-5.0, 5.0)
    ]
    for nx, ny in nodes:
        px, py = to_px(nx, ny)
        r = 4
        map_data[py-r:py+r, px-r:px+r] = 254

    # ---------------------------------------------------------
    # 3. 파일 저장 (Linux 호환성 위해 newline='\n' 명시)
    # ---------------------------------------------------------
    img_data = np.flipud(map_data)
    Image.fromarray(img_data).save("test_map.pgm")

    yaml_data = {
        'image': 'test_map.pgm',
        'mode': 'trinary',
        'resolution': resolution,
        'origin': [min_x, min_y, 0.0],
        'negate': 0,
        'occupied_thresh': 0.65,
        'free_thresh': 0.196
    }

    # Windows에서 실행해도 Linux 스타일 줄바꿈 강제
    with open("test_map.yaml", "w", newline='\n', encoding='utf-8') as f:
        yaml.dump(yaml_data, f, default_flow_style=False)

    # ---------------------------------------------------------
    # 4. Gazebo World 파일 생성
    # ---------------------------------------------------------
    world_content = """<?xml version="1.0"?>
<sdf version="1.6">
  <world name="default">
    <include>
      <uri>model://ground_plane</uri>
    </include>
    <include>
      <uri>model://sun</uri>
    </include>
    <physics type="ode">
      <real_time_update_rate>1000.0</real_time_update_rate>
      <max_step_size>0.001</max_step_size>
    </physics>
"""
    for i, (cx, cy, w, h) in enumerate(world_obstacles):
        height = 2.0
        world_content += f"""

    <model name='wall_{i}'>
      <pose>{cx} {cy} {height/2} 0 0 0</pose>
      <link name='link'>
        <collision name='collision'>
          <geometry>
            <box>
              <size>{w} {h} {height}</size>
            </box>
          </geometry>
        </collision>
        <visual name='visual'>
          <geometry>
            <box>
              <size>{w} {h} {height}</size>
            </box>
          </geometry>
          <material>
            <script>
              <uri>file://media/materials/scripts/gazebo.material</uri>
              <name>Gazebo/Grey</name>
            </script>
          </material>
        </visual>
      </link>
      <static>1</static>
    </model>
"""
    world_content += """
  </world>
</sdf>
"""
    with open("test_map.world", "w", newline='\n', encoding='utf-8') as f:
        f.write(world_content)

    print("생성 완료 (LF Line Endings Applied)")

if __name__ == '__main__':
    create_test_map()