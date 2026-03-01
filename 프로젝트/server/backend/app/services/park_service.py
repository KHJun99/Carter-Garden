from app.models.park_info import ParkInfo

def search_cars_by_number(number_fragment):
    # 차량 번호 뒷자리 검색 (또는 포함 검색)
    return ParkInfo.query.filter(ParkInfo.car_number.like(f'%{number_fragment}')).all()
