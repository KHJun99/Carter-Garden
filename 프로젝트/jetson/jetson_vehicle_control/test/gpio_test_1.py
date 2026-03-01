import Jetson.GPIO as GPIO
import time

# 핀 번호 (BOARD 모드 기준 29번)
PIN = 13

def main():
    GPIO.setmode(GPIO.BOARD)
    # 풀업 설정 (3.3V로 당겨놓고, 엔코더가 0V로 끌어내리는지 확인)
    GPIO.setup(PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    print(f"🔍 {PIN}번 핀 신호 감시 시작... (Ctrl+C로 종료)")
    print("바퀴를 아주 천천히 돌려보세요. 0과 1이 바뀌어야 합니다.")
    
    try:
        last_val = -1
        while True:
            current_val = GPIO.input(PIN)
            if current_val != last_val:
                print(f"신호 변경! -> {current_val}")
                last_val = current_val
            # time.sleep(0.01) # 0.01초마다 확인
    except KeyboardInterrupt:
        GPIO.cleanup()

if __name__ == '__main__':
    main()