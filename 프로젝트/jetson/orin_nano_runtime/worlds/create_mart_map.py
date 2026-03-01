import numpy as np
from PIL import Image
import yaml
import os

def create_mart_map():
    map_name = "mart"
    resolution = 0.05
    width_m, height_m = 8.0, 8.0
    width_px, height_px = int(width_m / resolution), int(height_m / resolution)
    map_data = np.full((height_px, width_px), 254, dtype=np.uint8)
    origin_x, origin_y = 4.0, 4.0 

    def to_px(x, y):
        px = int((x + origin_x) / resolution)
        py = int((y + origin_y) / resolution)
        return px, py

    def draw_box(x1, y1, x2, y2, value=0):
        p1x, p1y = to_px(x1, y1)
        p2x, p2y = to_px(x2, y2)
        map_data[min(p1y, p2y):max(p1y, p2y), min(p1x, p2x):max(p1x, p2x)] = value

    # 메인 룸 치수 (세로: 4.02m, 가로: 3.3m)
    x_min, x_max = -1.65, 1.65
    y_min, y_max = -2.01, 2.01
    t = 0.15 # 벽 두께

    # --- [1. 실제 벽 (검은색 실선)] ---
    draw_box(x_min-t, y_min-t, x_max+t, y_min) # 아래벽 (3.3m)
    draw_box(x_min-t, y_max, x_max+t, y_max+t) # 위벽 (3.3m)
    draw_box(x_min-t, y_min, x_min, y_max)     # 왼쪽벽 (4.02m)
    # 오른쪽 상단 진짜 벽 (1.1m 내려옴: 2.01 ~ 0.91)
    draw_box(x_max, 0.91, x_max+t, 2.01) 

    # --- [2. 가벽 (빨간색 실선 - 지도에만 표시)] ---
    # 입구 1 (0.8m): 0.91 ~ 0.11 (비워둠)
    # 가벽 (1.22m): 0.11 ~ -1.11 (검은색으로 칠함)
    draw_box(x_max, -1.11, x_max+t, 0.11) 
    # 입구 2 (0.9m): -1.11 ~ -2.01 (비워둠)
    
    # 우측 복도 가벽 구조 (폭 1.2m, 높이 2.92m)
    # 높이 2.92m는 y=0.91(입구1 시작)부터 y=-2.01(메인룸 끝)까지의 거리입니다.
    cor_x_end = x_max + 1.2
    draw_box(x_max, 0.91, cor_x_end+t, 0.91+t)    # 복도 위 가벽
    draw_box(x_max, -2.01-t, cor_x_end+t, -2.01)  # 복도 아래 가벽
    draw_box(cor_x_end, -2.01, cor_x_end+t, 0.91) # 복도 오른쪽 가벽

    # --- [3. 선반 배치 (blue_shelf)] ---
    # x 좌표: 벽에서 0.71m 간격
    s_x1_c = x_min + 0.71 + 0.17 # 좌측 열 중심 (-0.77)
    s_x2_c = s_x1_c + 0.34 + 0.71 # 우측 열 중심 (0.28)
    # y 좌표: 위에서 0.82m, 선반 사이 0.88m 간격
    s_y_top_c = y_max - 0.82 - 0.36 # 상단 행 중심 (0.83)
    s_y_bot_c = s_y_top_c - 0.72 - 0.88 # 하단 행 중심 (-0.77)

    draw_box(s_x1_c-0.17, s_y_top_c-0.36, s_x1_c+0.17, s_y_top_c+0.36) # 좌상
    draw_box(s_x2_c-0.17, s_y_top_c-0.36, s_x2_c+0.17, s_y_top_c+0.36) # 우상
    draw_box(s_x1_c-0.17, s_y_bot_c-0.36, s_x1_c+0.17, s_y_bot_c+0.36) # 좌하
    draw_box(s_x2_c-0.17, s_y_bot_c-0.36, s_x2_c+0.17, s_y_bot_c+0.36) # 우하

    img = Image.fromarray(np.flipud(map_data))
    img.save("mart.pgm")
    with open("mart.yaml", "w") as f:
        yaml.dump({'image': 'mart.pgm', 'mode': 'trinary', 'resolution': resolution, 
                   'origin': [-origin_x, -origin_y, 0.0], 'negate': 0, 
                   'occupied_thresh': 0.65, 'free_thresh': 0.196}, f)
    
    print("도면의 입구와 가벽 위치를 수정한 mart.pgm 및 mart.yaml 생성이 완료되었습니다.")

if __name__ == '__main__':
    create_mart_map()
