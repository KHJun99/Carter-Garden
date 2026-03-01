import smbus
import time

# ---------------------------------------------------------
# [중요] 아까 68이 떴던 버스 번호 '1'로 설정!
BUS_NUMBER = 1
# ---------------------------------------------------------

try:
    bus = smbus.SMBus(BUS_NUMBER)
    address = 0x68 # MPU6050 주소

    # 1. 센서 잠 깨우기 (Sleep 모드 해제)
    # 0x6B 레지스터에 0을 쓰면 센서가 일어납니다.
    bus.write_byte_data(address, 0x6B, 0)
    print("✅ 센서 연결 성공! 데이터를 읽어옵니다...")
    print("   (로봇을 손으로 흔들어 보세요!)")
    print("--------------------------------------")

    while True:
        # 2. 자이로(회전) 데이터 읽기 - Z축 (좌우 회전)
        # 상위 8비트(0x47)와 하위 8비트(0x48)를 읽어서 합칩니다.
        high = bus.read_byte_data(address, 0x47)
        low = bus.read_byte_data(address, 0x48)
        
        # 비트 연산으로 16비트 값 만들기
        value = (high << 8) | low
        
        # 음수 처리 (2의 보수)
        if value > 32768:
            value = value - 65536
            
        # 3. 가속도(기울기) 데이터 읽기 - X축 (앞뒤 기울기)
        acc_high = bus.read_byte_data(address, 0x3B)
        acc_low = bus.read_byte_data(address, 0x3C)
        acc_val = (acc_high << 8) | acc_low
        if acc_val > 32768:
            acc_val = acc_val - 65536

        # 보기 좋게 출력
        print(f"🔄 회전(Gyro Z): {value:6}  |  📉 기울기(Accel X): {acc_val:6}")
        time.sleep(0.1)

except Exception as e:
    print(f"❌ 에러 발생! 내용을 확인하세요: {e}")