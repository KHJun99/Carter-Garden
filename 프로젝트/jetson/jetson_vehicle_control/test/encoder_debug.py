import Jetson.GPIO as GPIO
import time

# 확인할 핀 번호 (BOARD 모드 기준 물리적 7번 핀)
TARGET_PIN = 7

def main():
    # 핀 번호 설정 (BOARD 모드)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(TARGET_PIN, GPIO.IN)
    
    print(f"🔍 [7번 핀] 신호 집중 모니터링 시작")
    print("바퀴를 손으로 천천히 돌려보세요.")
    print("정상이라면 '■ (HIGH)'와 '□ (LOW)'가 번갈아 나와야 합니다.")
    print("--------------------------------------------------")

    last_val = -1

    try:
        while True:
            # 7번 핀 값 읽기 (0 또는 1)
            current_val = GPIO.input(TARGET_PIN)
            
            # 이전 값과 다를 때만 출력 (상태 변화 감지)
            if current_val != last_val:
                state_visual = "■ (3.3V)" if current_val else "□ (0V)  "
                print(f"핀 {TARGET_PIN} 신호 변경: {state_visual}")
                
                last_val = current_val
            
            # CPU 점유율 방지용 아주 짧은 대기
            time.sleep(0.001) 
            
    except KeyboardInterrupt:
        GPIO.cleanup()
        print("\n👋 테스트를 종료합니다.")

if __name__ == '__main__':
    main()