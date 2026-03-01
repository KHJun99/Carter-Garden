# motor_hat.py - 직진 보정 기능 추가 (왼쪽 쏠림 해결용)
import board
import busio
from adafruit_pca9685 import PCA9685
from config import MOTOR_SAFE_SPEED, MOTOR_HAT_I2C_ADDRESS, PWM_FREQUENCY

class MotorDriverHat:
    def __init__(self):
        # 1. I2C 버스 연결
        self.i2c = busio.I2C(board.SCL, board.SDA)
        
        # 2. PCA9685 초기화
        self.pca = PCA9685(self.i2c, address=MOTOR_HAT_I2C_ADDRESS)
        self.pca.frequency = PWM_FREQUENCY
        
        # 3. 핀 설정 (이전 요청대로 왼쪽은 반전, 오른쪽은 정상)
        # [왼쪽 모터] (Motor A) - SW 반전 유지
        self.PWMA = self.pca.channels[0]
        self.AIN1 = self.pca.channels[2]
        self.AIN2 = self.pca.channels[1]
        
        # [오른쪽 모터] (Motor B) - 정상 유지
        self.BIN1 = self.pca.channels[3]
        self.BIN2 = self.pca.channels[4]
        self.PWMB = self.pca.channels[5]

        print(f"✅ Motor HAT 연결 완료 (직진 보정 적용됨)")

    def _set_motor(self, pwm_pin, in1_pin, in2_pin, speed):
        speed = max(-MOTOR_SAFE_SPEED, min(MOTOR_SAFE_SPEED, speed))
        duty = int(abs(speed) * 65535)
        pwm_pin.duty_cycle = duty
        
        if speed > 0:
            in1_pin.duty_cycle = 65535
            in2_pin.duty_cycle = 0
        elif speed < 0:
            in1_pin.duty_cycle = 0
            in2_pin.duty_cycle = 65535
        else:
            in1_pin.duty_cycle = 0
            in2_pin.duty_cycle = 0
            pwm_pin.duty_cycle = 0

    def straight(self, speed):
        # 🔧 [보정 구역] 왼쪽으로 휘면 -> 오른쪽 속도를 줄이세요!
        # 1.0은 100% 속도, 0.95는 95% 속도입니다.
        # 휘는 정도에 따라 0.95, 0.9, 0.85 식으로 숫자를 줄여보세요.
        
        LEFT_FACTOR = 1.0    # 왼쪽은 그대로
        RIGHT_FACTOR = 1.0      # 오른쪽을 90% 힘으로 줄임 (여기 숫자 조절!)

        self._set_motor(self.PWMA, self.AIN1, self.AIN2, speed * LEFT_FACTOR)
        self._set_motor(self.PWMB, self.BIN1, self.BIN2, speed * RIGHT_FACTOR)

    def drive(self, left_speed, right_speed):
        # 좌/우 모터를 독립 속도로 구동 (직진 보정/차동 제어용)
        self._set_motor(self.PWMA, self.AIN1, self.AIN2, left_speed)
        self._set_motor(self.PWMB, self.BIN1, self.BIN2, right_speed)

    def turn_left(self, speed):
        self._set_motor(self.PWMA, self.AIN1, self.AIN2, -speed)
        self._set_motor(self.PWMB, self.BIN1, self.BIN2, speed)

    def turn_right(self, speed):
        self._set_motor(self.PWMA, self.AIN1, self.AIN2, speed)
        self._set_motor(self.PWMB, self.BIN1, self.BIN2, -speed)

    def stop(self):
        self.straight(0)
