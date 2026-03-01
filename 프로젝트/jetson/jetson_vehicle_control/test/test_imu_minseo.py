import smbus
import time

# ---------------------------------------------------------
BUS_NUMBER = 1
# ---------------------------------------------------------

# 필터링 상수 (0.0 ~ 1.0)
# 값이 작을수록 더 부드러워지지만 반응이 느려짐 (0.7 ~ 0.9 추천)
ALPHA = 0.8 

def read_word_2c(bus, addr, reg):
    """16비트 데이터를 읽고 2의 보수(음수) 처리를 하는 함수"""
    high = bus.read_byte_data(addr, reg)
    low = bus.read_byte_data(addr, reg + 1)
    val = (high << 8) | low
    if val >= 0x8000:
        return -((65535 - val) + 1)
    else:
        return val

try:
    bus = smbus.SMBus(BUS_NUMBER)
    address = 0x68

    # 1. 센서 잠 깨우기
    bus.write_byte_data(address, 0x6B, 0)
    print("✅ 센서 연결 성공!")
    
    # ===================================================
    # [단계 1] 초기 캘리브레이션 (0점 잡기)
    # ===================================================
    print("--------------------------------------")
    print("🚧 초기 보정 중... 로봇을 움직이지 마세요! (약 2초)")
    
    cal_gyro_z = 0
    cal_count = 100
    
    for i in range(cal_count):
        # 자이로 Z축 (0x47)
        cal_gyro_z += read_word_2c(bus, address, 0x47)
        time.sleep(0.01)
        
    # 평균 오차 계산
    gyro_z_offset = cal_gyro_z / cal_count
    
    print(f"✅ 보정 완료! 감지된 오차(Offset): {gyro_z_offset:.2f}")
    print("--------------------------------------")

    # 필터링을 위한 이전 값 저장 변수
    last_gyro_z = 0

    while True:
        # ===================================================
        # [단계 2] 데이터 읽기 및 오차 제거
        # ===================================================
        raw_gyro_z = read_word_2c(bus, address, 0x47)
        raw_acc_x = read_word_2c(bus, address, 0x3B)

        # 캘리브레이션 값 빼기 (0점 조절)
        curr_gyro_z = raw_gyro_z - gyro_z_offset

        # ===================================================
        # [단계 3] 노이즈 필터링 (Low Pass Filter)
        # ===================================================
        # 공식: 현재값 = (이전값 * a) + (새로운값 * (1-a))
        # 갑자기 -250으로 튀는 값을 이전 값들이 잡아줍니다.
        if last_gyro_z == 0:
             filtered_gyro_z = curr_gyro_z # 첫 실행시는 그냥 대입
        else:
             filtered_gyro_z = (last_gyro_z * ALPHA) + (curr_gyro_z * (1 - ALPHA))
        
        # 다음 루프를 위해 현재 값을 저장
        last_gyro_z = filtered_gyro_z

        # ---------------------------------------------------
        # 보기 좋게 출력 (소수점 제거하여 깔끔하게)
        # ---------------------------------------------------
        # 튀는 값과 필터된 값을 비교해보세요.
        print(f"🔄 Z회전(보정됨): {int(filtered_gyro_z):6}  |  📉 기울기(X): {raw_acc_x:6}")
        
        time.sleep(0.1)

except Exception as e:
    print(f"❌ 에러 발생: {e}")