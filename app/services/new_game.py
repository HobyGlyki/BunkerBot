import random as match
from sqlalchemy.orm import Session
from app.DB.crud import get_random_bunker_items

def generate_game(db: Session):
    """
    Главная функция генерации катастрофы.
    Берет случайные предметы (еду и инвентарь) напрямую из БД.
    """
    # Достаем 5 предметов из базы. 
    # В БД еда и дичь записаны как INVENTORY, так что берем их одним запросом
    all_items = get_random_bunker_items(db, count=6)
    
    # На случай, если в базе вдруг оказалось мало предметов (защита от ошибок)
    while len(all_items) < 5:
        all_items.append("Неизвестная органическая масса")

    # Распределяем: 3 на еду, 2 на инвентарь бункера
    selected_eat = all_items[:3]
    selected_inventory = all_items[3:]

    eat_string = ", ".join(selected_eat)
    inv_string = ", ".join(selected_inventory)
    
    eat_count = match.randint(1, 10)
    bunker_years = match.randint(2, 12)
    
    result = {
        "human_left": match.randint(100, 13000000),
        "bunker_area": match.randint(100, 1000),
        "bunker_years": bunker_years,
        "bunker_capacity": match.randint(4, 6),
        "eat_items": eat_string,
        "eat_count": eat_count,
        "bunker_inventory": inv_string
    }
    return result

# Остальные мелкие функции (human_lost, bunker_size и т.д.) можно оставить как есть,
# а старые функции eat() и get_random_inventory() можно смело удалять, они больше не нужны.
def human_lost():
    return match.randint(100, 13000000)

def bunker_size():
    return match.randint(100, 1000) # В квадратных метрах

def bunker_time():
    return match.randint(2, 12) # от 2 до 12 лет

def bunker_size_h():
    return match.randint(4, 6) # Вместимость (количество выживших)

def eat():
    eat_nice = match.randint(0, len(EAT_LIST))
    eat_count = match.randint(1, 10) # На сколько лет хватит еды
    
    # Защита от выхода за пределы словаря (если выпадет ровно 100)
    
    return {
        "eat_nice": EAT_LIST[eat_nice],
        "eat_count": eat_count,
    }

def get_random_inventory():
    # Выбираем 2 случайных предмета из списка
    items = match.sample(bunker_items, 2)
    return ", ".join(items)



