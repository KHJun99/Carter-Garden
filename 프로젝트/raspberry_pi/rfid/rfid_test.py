#!/usr/bin/env python
# -*- coding: utf-8 -*-

import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

reader = SimpleMFRC522()

try:
    print("RFID 카드를 리더기에 가까이 대주세요...")
    card_id, text = reader.read()
    print(f"카드 ID: {card_id}")
    print(f"기록된 내용: {text}")
finally:
    GPIO.cleanup()