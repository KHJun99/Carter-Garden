import os
from PIL import Image

# 설정
TARGET_DIR = "images"
QUALITY = 80  # WebP 품질 (0~100, 보통 80이면 충분히 좋고 용량은 1/10 수준)

def convert_to_webp(directory):
    count = 0
    saved_space = 0

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                file_path = os.path.join(root, file)
                file_name, ext = os.path.splitext(file_path)
                webp_path = f"{file_name}.webp"

                # 이미 WebP가 있으면 건너뜀 (선택사항)
                if os.path.exists(webp_path):
                    continue

                try:
                    with Image.open(file_path) as img:
                        # PNG의 투명 배경 처리 (RGBA -> RGB 변환 시 검은 배경 방지)
                        if img.mode in ('RGBA', 'LA'):
                            background = Image.new(img.mode[:-1], img.size, (255, 255, 255))
                            background.paste(img, img.split()[-1])
                            img = background.convert('RGB')

                        # WebP로 저장
                        img.save(webp_path, 'webp', quality=QUALITY)

                        original_size = os.path.getsize(file_path)
                        webp_size = os.path.getsize(webp_path)
                        saved_space += (original_size - webp_size)

                        print(f"[변환 완료] {file} -> .webp ({original_size/1024:.1f}KB -> {webp_size/1024:.1f}KB)")
                        count += 1

                        # 원본 삭제 (원하시면 주석 해제)
                        # os.remove(file_path)

                except Exception as e:
                    print(f"[오류] {file}: {e}")

    print(f"\n총 {count}개 파일 변환 완료.")
    print(f"절약된 용량: {saved_space / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    convert_to_webp(TARGET_DIR)
