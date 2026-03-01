# 1_keyboard_control.py - SSH/터미널 전용 (수정됨)
import sys
import tty
import termios
import time
from config import SPEED_NORMAL
from motor_hat import MotorDriverHat

# 모터 드라이버 초기화
try:
    motor_hat = MotorDriverHat()
except Exception as e:
    print(f"❌ 모터 드라이버 초기화 실패: {e}")
    print("💡 팁: 'Device or resource busy' 에러라면 커널 드라이버 충돌입니다.")
    sys.exit(1)

def getch():
    """터미널에서 키 입력 하나를 바로 받아오는 함수 (엔터 필요 없음)"""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

print("========================================")
print("🚗 SSH 키보드 컨트롤러 시작")
print("----------------------------------------")
print(" [W] 전진   (계속 이동)")
print(" [X] 후진   (계속 이동)")
print(" [A] 좌회전 (제자리 턴)")
print(" [D] 우회전 (제자리 턴)")
print(" [SPACE] 또는 [S] 정지")
print(" [Q] 종료")
print("========================================")

try:
    while True:
        key = getch() # 키 입력 대기
        
        if key == 'w':
            print("🚗 전진 (Forward)")
            motor_hat.straight(-SPEED_NORMAL) # 방향 반대면 - 제거
        
        elif key == 'x':
            print("🔙 후진 (Backward)")
            motor_hat.straight(SPEED_NORMAL)  # 방향 반대면 - 추가
            
        elif key == 'a':
            print("↰ 좌회전 (Left)")
            motor_hat.turn_left(SPEED_NORMAL)
            
        elif key == 'd':
            print("↱ 우회전 (Right)")
            motor_hat.turn_right(SPEED_NORMAL)
            
        elif key == 's' or key == ' ':
            print("⏸️ 정지 (Stop)")
            motor_hat.stop()
            
        elif key == 'q':
            print("⏹️ 종료합니다.")
            break

except KeyboardInterrupt:
    pass
finally:
    motor_hat.stop()
    print("✅ 안전 정지 완료")