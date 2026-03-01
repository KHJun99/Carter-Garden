import sys
import os
import gc
import cv2
import torch
import numpy as np

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from rclpy.callback_groups import ReentrantCallbackGroup # 병렬 처리용
from rclpy.executors import MultiThreadedExecutor # 멀티스레드 실행기
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge
from vision_msgs.msg import Detection2DArray, Detection2D
from ultralytics import YOLO

# [환경 설정] 메모리 관리 및 CUDA 최적화
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:32,expandable_segments:True"
os.environ["CUDA_MODULE_LOADING"] = "LAZY"

current_dir = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(current_dir, 'models', 'monkey_model.pt') 

class SmartYoloDetector(Node):
    def __init__(self):
        super().__init__('smart_yolo_detector')

        # 영상 처리와 메시지 수신을 분리하여 키보드 주행 반응성 확보
        self.callback_group = ReentrantCallbackGroup()

        qos_fast = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.bridge = CvBridge()
        
        self.get_logger().info(f">>> 시연용 모델 로딩 중...: {MODEL_PATH}")
        try:
            self.yolo = YOLO(MODEL_PATH)
            if self.device.type == 'cuda':
                self.yolo.to(self.device).half() # 반정밀도 가속
                torch.backends.cudnn.benchmark = False # 연산 안정성 우선
        except Exception as e:
            self.get_logger().error(f"모델 로드 실패: {e}")
            sys.exit(1)

        self.is_active = False
        self.processing = False
        self.frame_count = 0

        # 구독 및 발행 설정 (병렬 처리 그룹 할당)
        self.sub = self.create_subscription(
            Image, '/image_raw', self.image_callback, qos_fast, callback_group=self.callback_group)
        self.result_pub = self.create_publisher(Image, '/yolo_result', 10) 
        self.pub = self.create_publisher(Detection2DArray, '/detections', 10)
        self.status_pub = self.create_publisher(String, '/robot/status', 10)
        self.mode_sub = self.create_subscription(
            String, '/robot/mode', self.mode_toggle_callback, 10, callback_group=self.callback_group)

        self.get_logger().info('>>> [안정성 & 부드러운 화면] 모드 가동')

    def mode_toggle_callback(self, msg):
        mode = msg.data.upper()
        if mode in ["REGISTER", "FOLLOW"]:
            self.is_active = True
            status_msg = String(); status_msg.data = "REGISTER_DONE"
            self.status_pub.publish(status_msg)
        elif mode in ["STOP", "IDLE"]:
            self.is_active = False
            if self.device.type == 'cuda': torch.cuda.empty_cache()

    def image_callback(self, msg):
        # 1. 활성화 상태가 아니거나 이미 처리 중이면 즉시 리턴
        if not self.is_active or self.processing:
            return

        # 2. [최적화] 프레임 스킵: 2프레임당 1개 처리 (시스템 부하 절반 감소)
        self.frame_count += 1
        if self.frame_count % 2 != 0:
            return

        self.processing = True
        
        try:
            # 이미지 변환
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            
            # YOLO 추론
            with torch.inference_mode():
                results = self.yolo.track(frame, persist=True, verbose=False, imgsz=320, 
                                          half=(self.device.type == 'cuda'), tracker="bytetrack.yaml")

            detection_array = Detection2DArray()
            detection_array.header = msg.header
            annotated_frame = results[0].plot()

            if results and results[0].boxes:
                boxes = results[0].boxes
                xywhs = boxes.xywh.cpu().numpy()
                clss = boxes.cls.cpu().numpy()
                confs = boxes.conf.cpu().numpy()
                ids = boxes.id.cpu().numpy() if boxes.id is not None else []
                
                target_idx = -1
                max_area = 0
                for i, bbox in enumerate(xywhs):
                    if int(clss[i]) == 0: # 원숭이 클래스 필터링
                        area = bbox[2] * bbox[3]
                        if area > max_area:
                            max_area = area
                            target_idx = i

                if target_idx != -1:
                    bbox = xywhs[target_idx]
                    obj_id = int(ids[target_idx]) if len(ids) > target_idx else -1
                    cx, cy, w, h = bbox
                    
                    det = Detection2D()
                    det.id = str(obj_id + 1000)
                    try:
                        det.bbox.center.position.x = float(cx)
                        det.bbox.center.position.y = float(cy)
                    except AttributeError:
                        det.bbox.center.x = float(cx); det.bbox.center.y = float(cy)
                    det.bbox.size_x = float(w); det.bbox.size_y = float(h)
                    detection_array.detections.append(det)

                    # 타겟 강조 (빨간 박스)
                    x1, y1 = int(cx - w/2), int(cy - h/2)
                    x2, y2 = int(cx + w/2), int(cy + h/2)
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 0, 255), 3)

            # 데이터 및 영상 발행
            self.pub.publish(detection_array)
            
            if self.result_pub.get_subscription_count() > 0:
                # [안정성 핵심] 해상도를 320x240으로 고정하여 전송 병목 차단
                view_frame = cv2.resize(annotated_frame, (320, 240))
                msg_raw = self.bridge.cv2_to_imgmsg(view_frame, encoding="bgr8")
                msg_raw.header = msg.header
                self.result_pub.publish(msg_raw)

        except Exception as e:
            self.get_logger().error(f"Error: {e}")
            
        finally:
            self.processing = False
            if self.frame_count % 200 == 0:
                gc.collect()

def main(args=None):
    rclpy.init(args=args)
    # 멀티스레드 실행기를 사용하여 키보드 주행 명령이 영상 처리 때문에 밀리지 않게 함
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

if __name__ == '__main__':
    main(sys.argv)