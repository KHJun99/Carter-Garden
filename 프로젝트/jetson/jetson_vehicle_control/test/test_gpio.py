import Jetson.GPIO as GPIO
import time

# 🔍 테스트할 핀 목록 (왼쪽: 7, 11 / 오른쪽: 13, 15)
TARGET_PINS = [7, 11, 13, 15]

# 핀 이름 매핑 (디버깅용)
PIN_NAMES = {
    7:  "LEFT_A  (7)",
    11: "LEFT_B  (11)",
    13: "RIGHT_A (13)",
    15: "RIGHT_B (15)"
}

def main():
    # 1. GPIO 설정
    GPIO.setmode(GPIO.BOARD)
    
    print("========================================")
    print("🚗 엔코더 4개 핀 동시 감시 시작")
    print(f"대상 핀: {TARGET_PINS}")
    print("바퀴를 돌리면 상태가 변할 때만 출력됩니다.")
    print("========================================")

    # 2. 모든 핀 입력 모드 설정 (내부 풀업 저항 사용)
    # 풀업(PUD_UP)을 걸어야 신호가 없을 때 3.3V로 잡혀서 노이즈가 줄어듭니다.
    for pin in TARGET_PINS:
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    
    # 3. 초기 상태 저장
    last_states = {pin: GPIO.input(pin) for pin in TARGET_PINS}

    try:
        while True:
            # 4. 모든 핀을 아주 빠르게 순회하며 상태 확인
            for pin in TARGET_PINS:
                current_val = GPIO.input(pin)
                
                # 상태가 이전과 다를 때만 출력 (Change detection)
                if current_val != last_states[pin]:
                    
                    # 시각적 효과 (1=■, 0=□)
                    visual = "■ (3.3V)" if current_val else "□ (0V)  "
                    pin_name = PIN_NAMES.get(pin, f"PIN {pin}")
                    
                    print(f"⚡ {pin_name} 변경됨 -> {visual}")
                    
                    # 상태 업데이트
                    last_states[pin] = current_val
            
            # CPU 과부하 방지 (0.001초 대기)
            time.sleep(0.001)

    except KeyboardInterrupt:
        print("\n👋 종료합니다. GPIO 정리 중...")
        GPIO.cleanup()

if __name__ == '__main__':
    main()