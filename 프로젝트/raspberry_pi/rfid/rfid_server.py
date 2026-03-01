import asyncio
import websockets
import sys
import pygame
import os
from mfrc522 import SimpleMFRC522

# 1. 경로 설정: 현재 파일(rfid_server.py) 위치 기준 같은 폴더 내 audio/beep.wav 지정
current_dir = os.path.dirname(os.path.abspath(__file__))
# S14P11D201/raspberry_pi/rfid -> S14P11D201/raspberry_pi/rfid/audio/beep.wav 로 경로 계산
sound_path = os.path.join(current_dir, "audio", "beep.wav")

# 2. pygame 오디오 초기화 (라즈베리 파이 5 및 USB 스피커 최적화)
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.mixer.init()

if os.path.exists(sound_path):
    beep_sound = pygame.mixer.Sound(sound_path)
    print(f"오디오 로드 완료: {sound_path}")
else:
    print(f"오류: 파일을 찾을 수 없습니다 -> {sound_path}")
    beep_sound = None

# RFID 리더기 객체 생성
reader = SimpleMFRC522()

async def rfid_scanner(websocket):
    print("Vue 앱 연결 완료. 스캔 대기 중...")
    try:
        while True:
            # RFID 카드 읽기 (Blocking 함수)
            id, text = reader.read()
            
            if text:
                product_id = text.strip()
                print(f"스캔된 상품 ID: {product_id}")
                
                # 3. 소리 재생 (USB 스피커 기본 장치로 출력)
                if beep_sound:
                    beep_sound.play()
                
                # 웹소켓 전송
                await websocket.send(product_id)
                
                # 연속 인식 방지 딜레이
                await asyncio.sleep(2)
                
    except Exception as e:
        print(f"RFID 읽기 오류: {e}")
    
async def main():
    # '0.0.0.0'으로 모든 네트워크 접속 허용
    async with websockets.serve(rfid_scanner, "0.0.0.0", 8765):
        print("RFID 웹소켓 서버가 8765 포트에서 시작되었습니다.")
        await asyncio.Future()  # 무한 실행

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("서버를 종료합니다.")