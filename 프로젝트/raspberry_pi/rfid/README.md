# RFID Module(RC522) - 라즈베리파이 연동

이 디렉토리는 상품 인식을 담당하는 RFID(RC522) 모듈의 연동 설정 및 테스트 코드를 관리합니다.

---

## 1. 하드웨어 설정

### ⚠️ 주의사항

* **전원 분리:** 반드시 라즈베리 파이의 전원을 끄고 연결하세요.
* **3.3V 연결:** 5V 핀에 연결할 경우 모듈이 영구적으로 손상될 수 있습니다.

### 핀 연결

| RC522 Pin | Raspberry Pi 4 Pin Name | Physical Pin No. |
| --- | --- | --- |
| **3.3V** | 3.3V Power | **1** |
| **RST** | GPIO 25 | **22** |
| **GND** | Ground | **6** |
| **MISO** | GPIO 9 (MISO) | **21** |
| **MOSI** | GPIO 10 (MOSI) | **19** |
| **SCK** | GPIO 11 (SCLK) | **23** |
| **SDA (SS)** | GPIO 8 (CE0) | **24** |

---

## 2. 환경 설정

### SPI 인터페이스 활성화

1. `sudo raspi-config` 실행
2. `3 Interface Options` → `I4 SPI` → `Yes` 선택
3. `sudo reboot` (재부팅 필수)
4. 확인: `ls /dev/spi*` 입력 시 `spidev0.0`, `spidev0.1` 확인

### 라이브러리 설치

```bash
# 시스템 패키지 업데이트 및 필수 드라이버 설치
sudo apt update
sudo apt install python3-pip python3-dev -y

# 필수 라이브러리 한꺼번에 설치
# websockets: 프론트엔드 통신용
# pygame: 비프음 재생용
# mfrc522: RFID 리더기 제어용
pip3 install spidev mfrc522 websockets pygame --break-system-packages

```

---

## 3. 파일 설명

현재 경로(`~/S14P11D201/raspberry_pi/rfid`)에 포함된 주요 스크립트입니다.

| 파일명 | 설명 |
| --- | --- |
| `rfid_test.py` | RFID 카드를 태깅하여 고유 ID(UID)와 저장된 Text를 읽어옵니다. |
| `rfid_write.py` | RFID 태그에 사용자 정의 데이터(product.id)를 기록합니다. |
| `rfid_server.py` | 실시간 상품 인식을 위한 웹소켓 서버를 실행하고 Vue 프런트엔드에 데이터를 전송합니다.(Vue 앱 실행 전 먼저 구동 필수) |

---

## 4. 실행 방법

1. **사운드 체크:** USB 스피커가 연결되어 있는지 확인합니다.
2. **서버 실행:**
```bash
python3 rfid_server.py
```
---

## 5. 트러블슈팅 (Pi 4 전용)

* **소리가 안 날 때:** `alsamixer` 명령어로 USB Audio가 기본 장치인지, 볼륨이 0은 아닌지 확인하세요.
* **인식이 안 될 때:** `lsmod | grep spi`를 통해 SPI 드라이버가 올라와 있는지 확인하고, 24번(SDA)과 22번(RST) 핀이 바뀌지 않았는지 체크하세요.

---

## 6. 추가 정보

상세 핀 맵 정보와 실제 연결 이미지 등 추가 자료는 아래 노션 페이지에 정리되어 있습니다.

* **자료실 바로가기:** [[노션 자료실](https://www.notion.so/RFID-2ed7577b27238029b367dc5c2882fd25)]


---

