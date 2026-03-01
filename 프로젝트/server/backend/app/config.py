import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Config:
    
    # Database 설정
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_HOST = os.getenv('DB_HOST')
    DB_NAME = os.getenv('DB_NAME')

    # 로컬 실행시
    DB_PORT = os.getenv('DB_PORT')

    if not DB_PASSWORD:
        raise ValueError("Error : .env 파일에 DB_PASSWORD가 없습니다!")

    # URI 생성
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}?charset=utf8mb4"
    # 로컬 실행시
    # SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # AWS S3
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = os.getenv('AWS_REGION', 'ap-northeast-2')
    AWS_BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')

    # Security
    SECRET_KEY = os.getenv('SECRET_KEY')

    # AI (GMS) 설정
    GMS_API_URL = os.environ.get('GMS_API_URL')
    GMS_API_KEY = os.environ.get('GMS_API_KEY')
    GMS_MODEL = os.environ.get('GMS_MODEL', 'gpt-5.2')

    # Payment (Toss)
    TOSS_SECRET_KEY = os.getenv('TOSS_SECRET_KEY')

    if not TOSS_SECRET_KEY:
        raise ValueError("Error : .env 파일에 TOSS_SECRET_KEY가 없습니다!")

    # 정적 파일 캐시 설정 (1일 = 86400초)
    SEND_FILE_MAX_AGE_DEFAULT = 86400
