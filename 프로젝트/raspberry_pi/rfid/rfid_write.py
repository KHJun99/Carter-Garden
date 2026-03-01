#!/usr/bin/env python
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

reader = SimpleMFRC522()

try:
    # 1. 입력받기
    text = input("스티커에 기록할 새로운 데이터를 입력하세요: ")
    print("이제 RFID 스티커를 리더기에 가까이 대주세요...")
    
    # 2. 데이터 쓰기
    reader.write(text)
    print("성공적으로 기록되었습니다!")

finally:
    # 3. 설정 초기화
    GPIO.cleanup()