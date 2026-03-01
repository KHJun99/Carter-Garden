from datetime import datetime

def get_current_time():
    """현재 시간을 반환합니다."""
    return datetime.now()

def format_datetime(dt):
    """datetime 객체를 문자열 포맷으로 변환합니다."""
    if not dt:
        return None
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def is_expired(expire_date):
    """만료 여부를 확인합니다."""
    return datetime.now() > expire_date