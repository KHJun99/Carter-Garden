import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
import smbus
import math
import time

# --- 설정 (아까 확인한 버스 번호로 수정하세요!) ---
I2C_BUS = 1  
device_address = 0x68

# MPU-6050 레지스터 주소
PWR_MGMT_1   = 0x6B
SMPLRT_DIV   = 0x19
CONFIG       = 0x1A
GYRO_CONFIG  = 0x1B
INT_ENABLE   = 0x38
ACCEL_XOUT_H = 0x3B
ACCEL_YOUT_H = 0x3D
ACCEL_ZOUT_H = 0x3F
GYRO_XOUT_H  = 0x43
GYRO_YOUT_H  = 0x45
GYRO_ZOUT_H  = 0x47

class IMUPublisher(Node):
    def __init__(self):
        super().__init__('imu_publisher')
        self.publisher_ = self.create_publisher(Imu, 'imu/data', 10)
        self.timer = self.create_timer(0.05, self.timer_callback) # 20Hz

        try:
            self.bus = smbus.SMBus(I2C_BUS)
            self.init_mpu()
            # Gyro Z bias calibration (robot must be still)
            self.gyro_z_bias = self.calibrate_gyro_z(samples=200, delay=0.005)
            # Low-pass filter state
            self.gyro_z_filtered = 0.0
            self.lpf_alpha = 0.9
            print(f"✅ IMU(MPU-6050) 노드 시작! (Bus: {I2C_BUS})")
        except Exception as e:
            print(f"🚨 센서 연결 실패! 버스 번호를 확인하세요. ({e})")

    def init_mpu(self):
        # MPU6050 깨우기
        self.bus.write_byte_data(device_address, SMPLRT_DIV, 7)
        self.bus.write_byte_data(device_address, PWR_MGMT_1, 1)
        self.bus.write_byte_data(device_address, CONFIG, 0)
        self.bus.write_byte_data(device_address, GYRO_CONFIG, 24)
        self.bus.write_byte_data(device_address, INT_ENABLE, 1)

    def read_raw_data(self, addr):
        # 16비트 데이터 읽기
        high = self.bus.read_byte_data(device_address, addr)
        low = self.bus.read_byte_data(device_address, addr+1)
        value = ((high << 8) | low)
        if(value > 32768):
            value = value - 65536
        return value

    def calibrate_gyro_z(self, samples=200, delay=0.005):
        total = 0
        for _ in range(samples):
            total += self.read_raw_data(GYRO_ZOUT_H)
            time.sleep(delay)
        bias = total / samples if samples > 0 else 0.0
        print(f"✅ Gyro Z bias calibrated: {bias:.2f}")
        return bias

    def timer_callback(self):
        msg = Imu()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "imu_link"

        # 가속도 읽기 (단위 변환: LSB -> m/s^2)
        acc_x = self.read_raw_data(ACCEL_XOUT_H)
        acc_y = self.read_raw_data(ACCEL_YOUT_H)
        acc_z = self.read_raw_data(ACCEL_ZOUT_H)

        msg.linear_acceleration.x = acc_x / 16384.0 * 9.81
        msg.linear_acceleration.y = acc_y / 16384.0 * 9.81
        msg.linear_acceleration.z = acc_z / 16384.0 * 9.81

        # 자이로 읽기 (단위 변환: LSB -> rad/s)
        gyro_x = self.read_raw_data(GYRO_XOUT_H)
        gyro_y = self.read_raw_data(GYRO_YOUT_H)
        gyro_z = self.read_raw_data(GYRO_ZOUT_H) - self.gyro_z_bias

        # Low-pass filter to reduce noise spikes
        self.gyro_z_filtered = (self.lpf_alpha * self.gyro_z_filtered) + ((1 - self.lpf_alpha) * gyro_z)

        msg.angular_velocity.x = gyro_x / 131.0 * (math.pi / 180.0)
        msg.angular_velocity.y = gyro_y / 131.0 * (math.pi / 180.0)
        msg.angular_velocity.z = self.gyro_z_filtered / 131.0 * (math.pi / 180.0)

        # No valid orientation provided (use gyro integration)
        msg.orientation_covariance = [-1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        
        self.publisher_.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = IMUPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
