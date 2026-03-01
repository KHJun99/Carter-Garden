import numpy as np
from PIL import Image
import yaml

def create_map():
    resolution = 0.1
    margin = 2.0
    total_size = 14.0  # 10m(기존) + 2m(왼쪽) + 2m(오른쪽)
    
    dim = int(total_size / resolution)
    map_data = np.full((dim, dim), 254, dtype=np.uint8)

    # 외곽 벽 (0: 장애물)
    map_data[0:2, :] = 0; map_data[-2:, :] = 0
    map_data[:, 0:2] = 0; map_data[:, -2:] = 0

    def to_px(m): return int((m + margin) / resolution)

    # 장애물 A (2,2) ~ (4,4)
    map_data[to_px(2.0):to_px(4.0), to_px(2.0):to_px(4.0)] = 0
    # 장애물 B (6,6) ~ (8,8)
    map_data[to_px(6.0):to_px(8.0), to_px(6.0):to_px(8.0)] = 0

    map_data = np.flipud(map_data)
    Image.fromarray(map_data).save("test_map.pgm")

    yaml_data = {
        'image': 'test_map.pgm',
        'mode': 'trinary',
        'resolution': resolution,
        'origin': [-margin, -margin, 0.0],
        'negate': 0,
        'occupied_thresh': 0.65,
        'free_thresh': 0.196
    }

    with open("test_map.yaml", "w") as f:
        yaml.dump(yaml_data, f, default_flow_style=False)

    print("맵 파일 생성 완료.")

if __name__ == '__main__':
    create_map()
