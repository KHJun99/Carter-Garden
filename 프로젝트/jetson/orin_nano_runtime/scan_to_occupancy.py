#!/usr/bin/env python3
"""scan_to_occupancy.py
- 입력: slam_points_N.npz (x, y arrays)
- 출력: slam_map_N.pgm, slam_map_N.yaml
- 옵션: --publish (ROS2로 /map에 OccupancyGrid 퍼블리시)
"""
import argparse
import numpy as np
import os
from PIL import Image

try:
    import rclpy
    from rclpy.node import Node
    from std_msgs.msg import Header
    from nav_msgs.msg import OccupancyGrid, MapMetaData
    from geometry_msgs.msg import Pose
    ROS2_AVAILABLE = True
except Exception:
    ROS2_AVAILABLE = False


def points_to_grid(x, y, resolution=0.05, margin=2.0):
    # x,y in meters
    xs = np.array(x)
    ys = np.array(y)
    if xs.size == 0:
        raise ValueError("No points provided")

    xmin = xs.min() - margin
    xmax = xs.max() + margin
    ymin = ys.min() - margin
    ymax = ys.max() + margin

    width = int(np.ceil((xmax - xmin) / resolution))
    height = int(np.ceil((ymax - ymin) / resolution))

    grid = np.zeros((height, width), dtype=np.uint8)  # 0 = free

    # Convert points to indices
    ix = ((xs - xmin) / resolution).astype(int)
    iy = ((ys - ymin) / resolution).astype(int)

    # Clip
    ix = np.clip(ix, 0, width - 1)
    iy = np.clip(iy, 0, height - 1)

    # Mark occupied cells (100)
    grid[iy, ix] = 100

    origin = (xmin, ymin)
    return grid, origin, resolution


def save_pgm(grid, path):
    # grid expected as numpy uint8
    im = Image.fromarray(grid[::-1, :])  # flip vertically for correct origin
    im = im.convert('L')
    # let PIL infer format from extension (PGM)
    im.save(path)


def save_yaml(pgm_path, yaml_path, resolution, origin):
    content = f"image: {os.path.basename(pgm_path)}\n"
    content += f"resolution: {resolution}\n"
    content += f"origin: [{origin[0]}, {origin[1]}, 0.0]\n"
    content += "negate: 0\n"
    content += "occupied_thresh: 0.65\n"
    content += "free_thresh: 0.196\n"
    with open(yaml_path, 'w') as f:
        f.write(content)


class MapPublisher(Node):
    def __init__(self, grid, origin, resolution, frame_id='map'):
        super().__init__('scan_to_map_publisher')
        self.pub = self.create_publisher(OccupancyGrid, 'map', 10)
        self.timer = self.create_timer(1.0, self.timer_cb)
        self.grid = grid
        self.origin = origin
        self.resolution = resolution
        self.frame_id = frame_id

    def timer_cb(self):
        msg = OccupancyGrid()
        header = Header()
        header.stamp = self.get_clock().now().to_msg()
        header.frame_id = self.frame_id
        msg.header = header

        meta = MapMetaData()
        meta.resolution = self.resolution
        meta.width = int(self.grid.shape[1])
        meta.height = int(self.grid.shape[0])
        pose = Pose()
        pose.position.x = self.origin[0]
        pose.position.y = self.origin[1]
        pose.position.z = 0.0
        meta.origin = pose
        msg.info = meta

        # Flatten grid top->bottom expected by ROS (row-major)
        flat = self.grid[::-1, :].flatten()
        # Convert 0->0, 100->100, unknown as -1 (we don't use unknown here)
        ros_data = [int(v) if v != 255 else -1 for v in flat]
        msg.data = ros_data

        self.pub.publish(msg)
        self.get_logger().info('Published OccupancyGrid')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('npz', help='Input .npz file with x and y arrays')
    parser.add_argument('--resolution', type=float, default=0.05)
    parser.add_argument('--margin', type=float, default=2.0)
    parser.add_argument('--publish', action='store_true', help='Publish /map via ROS2')
    args = parser.parse_args()

    data = np.load(args.npz)
    x = data['x']
    y = data['y']

    grid, origin, res = points_to_grid(x, y, resolution=args.resolution, margin=args.margin)

    base = os.path.splitext(os.path.basename(args.npz))[0].replace('slam_points_', 'slam_map_')
    pgm_path = base + '.pgm'
    yaml_path = base + '.yaml'

    save_pgm(grid, pgm_path)
    save_yaml(pgm_path, yaml_path, res, origin)

    print(f'Saved: {pgm_path} and {yaml_path}')

    if args.publish:
        if not ROS2_AVAILABLE:
            print('ROS2 not available in this Python environment.')
            return
        rclpy.init()
        node = MapPublisher(grid, origin, res)
        try:
            rclpy.spin(node)
        except KeyboardInterrupt:
            pass
        finally:
            node.destroy_node()
            rclpy.shutdown()


if __name__ == '__main__':
    main()
