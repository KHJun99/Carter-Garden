import asyncio
import websockets
import sys

# 이 스크립트는 PC/WSL 환경에서 하드웨어 없이 RFID 기능을 테스트하기 위한 모의 서버입니다.
# 터미널에 상품 ID(예: 8801234567890)를 입력하고 엔터를 치면, 
# 실제 RFID가 찍힌 것처럼 프론트엔드에 데이터를 전송합니다.

async def rfid_mock_scanner(websocket):
    print(">>> [MOCK MODE] 가상 RFID 서버가 연결되었습니다.")
    print(">>> 테스트 방법: 아래에 상품 ID를 입력하고 Enter를 누르세요.")
    
    try:
        while True:
            # 터미널 입력을 기다립니다 (Blocking 방지를 위해 Executor 사용)
            product_id = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            product_id = product_id.strip()
            
            if product_id:
                print(f">>> 전송 중: [{product_id}]")
                await websocket.send(product_id)
                print(">>> 전송 완료! 다음 ID를 입력하세요.")
                
    except websockets.exceptions.ConnectionClosed:
        print(">>> 클라이언트(프론트엔드) 연결이 끊어졌습니다.")
    except Exception as e:
        print(f">>> 오류 발생: {e}")

async def main():
    print("==================================================")
    print("      SMART CART - RFID MOCK SERVER (TEST)        ")
    print("==================================================")
    print("ws://localhost:8765 포트에서 대기 중...")
    
    async with websockets.serve(rfid_mock_scanner, "0.0.0.0", 8765):
        await asyncio.Future()  # 무한 대기

if __name__ == "__main__":
    try:
        if sys.platform == 'win32':
            # 윈도우의 경우 이벤트 루프 정책 설정 필요 가능성 있음
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n>>> 서버를 종료합니다.")
