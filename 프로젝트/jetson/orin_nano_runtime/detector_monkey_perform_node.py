import gc
import os
import sys
from typing import List, Optional

import cv2
import torch

import rclpy
from cv_bridge import CvBridge
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import Image
from std_msgs.msg import String
from ultralytics import YOLO
from vision_msgs.msg import Detection2D, Detection2DArray

# GPU 메모리 안전 설정
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "max_split_size_mb:32,expandable_segments:True")
os.environ.setdefault("CUDA_MODULE_LOADING", "LAZY")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(CURRENT_DIR, "models", "monkey_model.pt")

class SmartYoloDetector(Node):
    def __init__(self) -> None:
        super().__init__("smart_yolo_detector_perform")

        # 파라미터 선언
        self.declare_parameter("image_topic", "/image_raw")
        self.declare_parameter("result_topic", "/yolo_result")
        self.declare_parameter("detection_topic", "/detections")
        self.declare_parameter("status_topic", "/robot/status")
        self.declare_parameter("mode_topic", "/robot/mode")
        self.declare_parameter("imgsz", 416)
        self.declare_parameter("conf_thres", 0.35)
        self.declare_parameter("iou_thres", 0.5)
        self.declare_parameter("frame_skip", 1)
        self.declare_parameter("start_active", False)

        self.image_topic = self.get_parameter("image_topic").value
        self.result_topic = self.get_parameter("result_topic").value
        self.detection_topic = self.get_parameter("detection_topic").value
        self.status_topic = self.get_parameter("status_topic").value
        self.mode_topic = self.get_parameter("mode_topic").value

        self.imgsz = int(self.get_parameter("imgsz").value)
        self.conf_thres = float(self.get_parameter("conf_thres").value)
        self.iou_thres = float(self.get_parameter("iou_thres").value)
        self.frame_skip = max(1, int(self.get_parameter("frame_skip").value))
        self.start_active = bool(self.get_parameter("start_active").value)

        qos_fast = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.bridge = CvBridge()
        self.is_active = self.start_active
        self.processing = False
        self.frame_count = 0
        self.total_rx_frames = 0
        self.published_frames = 0
        self.last_mode = "INIT"

        self.get_logger().info(f"모델 로딩: {MODEL_PATH}")
        self.yolo = YOLO(MODEL_PATH)
        if self.device.type == "cuda":
            self.yolo.to("cuda")
            torch.backends.cudnn.benchmark = True

        self.image_sub = self.create_subscription(Image, self.image_topic, self.image_callback, qos_fast)
        self.mode_sub = self.create_subscription(String, self.mode_topic, self.mode_callback, 10)
        self.result_pub = self.create_publisher(Image, self.result_topic, 10)
        self.det_pub = self.create_publisher(Detection2DArray, self.detection_topic, 10)
        self.status_pub = self.create_publisher(String, self.status_topic, 10)
        self.debug_timer = self.create_timer(5.0, self.debug_tick)

        self.get_logger().info(
            f"감지기 준비 완료 (device={self.device.type}, imgsz={self.imgsz}, conf={self.conf_thres}, frame_skip={self.frame_skip}, active={self.is_active})"
        )

    def mode_callback(self, msg: String) -> None:
        mode = msg.data.strip().upper()
        prev_active = self.is_active
        self.last_mode = mode
        self.get_logger().info(f"[모드] 수신: {mode}, 이전 활성 상태: {prev_active}")

        if mode == "REGISTER":
            self.is_active = True
            done = String()
            done.data = "REGISTER_DONE"
            self.status_pub.publish(done)
            self.get_logger().info("[모드] REGISTER -> 감지 활성화, REGISTER_DONE 전송")
            return

        if mode in ("STOP", "IDLE"):
            self.is_active = False
            if self.device.type == "cuda":
                torch.cuda.empty_cache()
            self.get_logger().info(f"[모드] {mode} -> 감지 비활성화")
            return

        self.get_logger().info(f"[모드] 무시: {mode}, 현재 상태: {self.is_active}")

    def image_callback(self, msg: Image) -> None:
        self.total_rx_frames += 1
        if not self.is_active or self.processing:
            return

        self.frame_count += 1
        if self.frame_count % self.frame_skip != 0:
            return

        self.processing = True
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")

            results = self.yolo.predict(
                source=frame,
                imgsz=self.imgsz,
                conf=self.conf_thres,
                iou=self.iou_thres,
                classes=[0],
                verbose=False,
                half=(self.device.type == "cuda"),
                device=0 if self.device.type == "cuda" else "cpu",
            )

            det_arr = Detection2DArray()
            det_arr.header = msg.header

            annotated_frame = frame
            if results:
                result = results[0]
                annotated_frame = result.plot()
                boxes = result.boxes
                if boxes is not None and len(boxes) > 0:
                    xywhs = boxes.xywh.detach().cpu().numpy()
                    confs = boxes.conf.detach().cpu().numpy()
                    xyxys = boxes.xyxy.detach().cpu().numpy()

                    for i, (bbox, conf) in enumerate(zip(xywhs, confs)):
                        cx, cy, w, h = bbox

                        if conf >= 0.90:
                            x1, y1, x2, y2 = map(int, xyxys[i])
                            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                            cv2.putText(annotated_frame, f"Match: {conf:.2f}", (x1, max(0, y1 - 10)),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                        det = Detection2D()
                        det.id = str(i + 1000)

                        try:
                            det.bbox.center.position.x = float(cx)
                            det.bbox.center.position.y = float(cy)
                        except AttributeError:
                            det.bbox.center.x = float(cx)
                            det.bbox.center.y = float(cy)

                        det.bbox.size_x = float(w)
                        det.bbox.size_y = float(h)
                        det_arr.detections.append(det)

            self.det_pub.publish(det_arr)

            if self.result_pub.get_subscription_count() > 0:
                view = cv2.resize(annotated_frame, (320, 240))
                view_msg = self.bridge.cv2_to_imgmsg(view, encoding="bgr8")
                view_msg.header = msg.header
                self.result_pub.publish(view_msg)
                self.published_frames += 1

        except Exception as exc:
            self.get_logger().error(f"감지 오류: {exc}")
        finally:
            self.processing = False
            if self.frame_count % 200 == 0:
                gc.collect()

    def debug_tick(self) -> None:
        self.get_logger().info(
            f"[디버그] active={self.is_active} mode={self.last_mode} "
            f"rx={self.total_rx_frames} proc={self.frame_count} pub={self.published_frames} "
            f"subs={self.result_pub.get_subscription_count()}"
        )

def main(args: Optional[List[str]] = None) -> None:
    rclpy.init(args=args)
    executor = MultiThreadedExecutor()
    node = SmartYoloDetector()
    executor.add_node(node)

    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main(sys.argv)
