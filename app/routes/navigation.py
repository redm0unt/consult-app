from typing import List, Tuple

_Page = Tuple[str, str]

def get_pages() -> List[_Page]:
    return [
        ('Главная', 'main.index'),
        ('Мероприятия', 'main.index'),
        ('Учителя', 'main.teachers'),
        ('Здания', 'main.index'),
    ]
