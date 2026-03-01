import numpy as np
from PIL import Image
import yaml
import os

def create_map():
    # 맵 설정 (미터 단위)
    resolution = 0.05
    margin = 2.0  # 여백
    
    # 좌표 범위 (SQL 데이터 기반)
    # X: -6.0 ~ 9.0  -> 폭 약 15m
    # Y: -5.0 ~ 25.0 -> 높이 약 30m
    min_x, max_x = -10.0, 15.0
    min_y, max_y = -10.0, 30.0
    
    width_m = max_x - min_x
    height_m = max_y - min_y
    
    width_px = int(width_m / resolution)
    height_px = int(height_m / resolution)
    
    print(f"맵 크기: {width_m}m x {height_m}m ({width_px}px x {height_px}px)")
    
    # 254: Free space (흰색)
    map_data = np.full((height_px, width_px), 254, dtype=np.uint8)
    
    # 좌표 변환 함수 (World -> Pixel)
    # 이미지 원점은 좌상단이므로 y축 반전 필요
    # 그러나 PGM/YAML 표준에서는 원점(origin)을 지정하면 됨.
    # 여기서는 배열 인덱싱 편의를 위해 (0,0)을 맵의 좌하단으로 가정하고 그림.
    def to_px(x, y):
        px = int((x - min_x) / resolution)
        py = int((y - min_y) / resolution)
        return px, py

    # 1. 외곽 벽 그리기 (0: Obstacle, 검은색)
    wall_thickness_px = 5
    map_data[0:wall_thickness_px, :] = 0
    map_data[-wall_thickness_px:, :] = 0
    map_data[:, 0:wall_thickness_px] = 0
    map_data[:, -wall_thickness_px:] = 0
    
    # 2. SQL 데이터의 주요 포인트에 작은 장애물(기둥) 추가 (옵션)
    # 코너나 진열대 위치를 표시하여 시뮬레이션에서 인식 가능하게 함
    obstacles = [
        (-6.0, 10.0), (-6.0, 25.0), (6.0, 25.0), (6.0, 10.0), # Corners
        (0.0, 10.0), (-6.0, 17.5), (6.0, 17.5), (-2.0, 25.0), (2.0, 25.0) # Shelves
    ]
    
    obstacle_radius_px = 4 # 20cm
    for ox, oy in obstacles:
        px, py = to_px(ox, oy)
        # 사각형 장애물
        r = obstacle_radius_px
        # 배열 범위 체크
        y_start = max(0, py-r)
        y_end = min(height_px, py+r)
        x_start = max(0, px-r)
        x_end = min(width_px, px+r)
        map_data[y_start:y_end, x_start:x_end] = 0

    # 3. 이미지 저장
    # PGM은 (0,0)이 좌상단. 배열의 (0,0)은 데이터상 좌하단(YAML origin 기준)이어야 매칭이 쉬움.
    # 하지만 보통 flipud를 해서 저장함.
    # YAML origin은 맵의 좌하단(Left-Bottom)의 World 좌표.
    
    # 이미지를 상하 반전시켜서 저장 (배열의 0행이 이미지의 맨 위가 되도록, 
    # 하지만 우리의 로직(y 증가 시 위로)과 맞추려면, 배열의 0행은 y_min이어야 하고,
    # 이미지 저장 시에는 이것이 맨 아래로 가야 함. -> flipud 필요)
    img = Image.fromarray(np.flipud(map_data))
    img.save("my_map.pgm")
    
    # 4. YAML 파일 생성
    yaml_data = {
        'image': 'my_map.pgm',
        'mode': 'trinary',
        'resolution': resolution,
        'origin': [min_x, min_y, 0.0], # 맵의 좌하단 좌표
        'negate': 0,
        'occupied_thresh': 0.65,
        'free_thresh': 0.196
    }
    
    with open("my_map.yaml", "w") as f:
        yaml.dump(yaml_data, f, default_flow_style=False)
        
    print("맵 생성 완료: my_map.pgm, my_map.yaml")

if __name__ == '__main__':
    create_map()
