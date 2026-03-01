import Jetson.GPIO as GPIO
import time

# 핀 설정 (왼쪽: 7/11, 오른쪽: 13/15)
LEFT_A = 7
LEFT_B = 11
RIGHT_A = 13
RIGHT_B = 15

# 카운트 변수 (전역 변수)
left_count = 0
right_count = 0

def main():
    global left_count, right_count
    
    GPIO.setmode(GPIO.BOARD)
    
    # 핀 설정 (입력 모드)
    # 물리 저항이 있으므로 소프트웨어 풀업은 끕니다(PUD_OFF).
    pins = [LEFT_A, LEFT_B, RIGHT_A, RIGHT_B]
    for pin in pins:
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_OFF)

    # 인터럽트 핸들러 (신호가 바뀔 때만 실행되는 함수)
    def left_callback(channel):
        global left_count
        # A와 B의 상태를 비교해서 방향 결정 (간이 로직)
        if GPIO.input(LEFT_A) == GPIO.input(LEFT_B):
            left_count += 1
        else:
            left_count -= 1

    def right_callback(channel):
        global right_count
        if GPIO.input(RIGHT_A) == GPIO.input(RIGHT_B):
            right_count += 1
        else:
            right_count -= 1

    # 이벤트 감지 등록 (A상 핀의 변화를 감지)
    # RISING/FALLING 모두 감지 (BOTH)
    GPIO.add_event_detect(LEFT_A, GPIO.BOTH, callback=left_callback)
    GPIO.add_event_detect(RIGHT_A, GPIO.BOTH, callback=right_callback)

    print("🚀 엔코더 카운팅 시작! 바퀴를 굴려보세요.")
    print("----------------------------------------")

    try:
        while True:
            # 0.1초마다 현재 카운트 출력
            print(f"Left: {left_count}  |  Right: {right_count}")
            time.sleep(0.1)

    except KeyboardInterrupt:
        GPIO.cleanup()
        print("\n종료합니다.")

if __name__ == '__main__':
    main()