from operator import is_
import random as match   

# Основная Функция генерации карт

def generate_full_character():
    """
    Главная функция генерации персонажа.
    Собирает все характеристики (8 базовых карт) + 2 спец-способности.
    Возвращает готовый словарь для записи в БД или отправки в ИИ.
    """
    character = {
        "biology": card_biology(),       # Пол, возраст, раса
        "appearance": card_appearance(), # Внешность, рост, масса
        "health": card_heal(),           # Состояние здоровья
        "job": card_job(),               # Работа и навык
        "hobby": card_hobby(),           # Увлечение
        "fact": card_fact(),             # Факт биографии
        "phobia": card_phobia(),         # Страх
        "inventory_1": inventory(),      # Малый инвентарь
        "inventory_2": inventory(),      # Большой инвентарь (или второй предмет)
        
        # Две спец-способности (Ability1 и Ability2)
        # В БД мы запишем их обе под типом ABILITY, но здесь разделяем для удобства
        "ability_1": card_ability(),
        "ability_2": card_ability()
    }
    return character

# Функция для хаоса игры

def generate_chaos_card(chaos_level: int = None):
    """
    Генерирует карту хаоса в зависимости от уровня хаоса.
    Чем выше уровень хаоса, тем более абсурдной будет карта.
    """

    if chaos_level is None:
        chaos_level = match.randint(0, 100)
    
    chaos_level = min(chaos_level, 100)
    
    chaos_card = {
        "chaos_description": chaos[chaos_level//20],  # Используем словарь chaos для описания
        "chaos_level": chaos_level
    }
    return chaos_card

# Генерация отдельной карты

def skill_ability(ability):
    skilln = match.randint(0, 5)
    power_level = match.randint(0, 15) * skilln

    skill = SkillType[skilln]

    card_ability = {
        "ability": AbilityType[ability],
        "skill": skill,
        'power_level': power_level
    }

    return card_ability


def card_biology():
    gender = match.randint(0, 1)

    rasen = match.randint(0, 13)

    if  rasen > 2:
        y = 20
        x = 1000
    else:
        y = 10
        x = 75
    old = match.randint(y, x)
    
    card_biology = {
        "gender": nice[gender],
        "old": old,
        "race": rase[rasen]
    }

    return card_biology

def card_appearance():
    is_nice =   match.randint(0, 1)
    appearancen = match.randint(0, 100)

    height_cm = match.randint(140, 350)
    height_m = height_cm / 100


    if is_nice:
        # Идеальные пропорции (ИМТ от 18.5 до 24.9)
        bmi = match.uniform(18.5, 25.0)
        # x1 = 50, x2 = 90 из твоего черновика тут не нужны, 
        # формула сама подберет вес под рост.
    else:
        # Абсурдные пропорции (либо очень худой, либо очень толстый)
        # Рандомим: 0 - истощение, 1 - тяжелый вес
        if match.random() > 0.5:
            bmi = match.uniform(10.0, 15.0)  # Очень худой
        else:
            bmi = match.uniform(40.0, 70.0)
        
    mass = int(bmi * (height_m ** 2))
    
    realistic_mass = appearancen * 3
    if not is_nice:
        mass = min(mass, realistic_mass)

    card_appearance = {
        "appearance": appearance[appearancen//20],
        "is_nice": nice[is_nice],
        "mass": mass,
        "height": height_cm
    }

    return card_appearance

def card_heal():
    healx = match.randint(0, 100)
    is_appearance = match.randint(0, 2)

    if healx > 90:
        healx = 100
        is_appearance = 3


    

    card_heal = {
        "heal": heal[healx//20],
        "is_appearance": heal_appearance[is_appearance]

    }

    return card_heal

def card_job():
    is_job_nice = match.randint(0, 1)
    job_val = match.randint(0, 100)
    if is_job_nice:
        js_job_nece = "полезная"
        if job_val//20 > 2:
            scill = job_val//20
        else:
            scill = 0
    else: 
        scill = 0
        js_job_nece = "Бесполезная"

    card_job = {
        "job": job[job_val//20],
        "is_nice": js_job_nece,
        "scill": scill
    }

    return card_job

def card_hobby():
    is_job = match.randint(0, 1)
    hobby = match.randint(0, 100)
    is_nice = match.randint(0, 1)

    card_hobby = {
        "hobby": appearance[hobby//20],
        "is_nice": nice[is_nice],
        "is_job": nice[is_job]
    }

    return card_hobby

def card_fact():
    is_positive = match.randint(0, 1)
    is_inexpected = match.randint(0, 1) # 0 - факт не неожиданный, 1 - факт неожиданный
    chaosn = match.randint(0, 100)

    if chaosn > 85:
        chaosn =  100
    else:
        chaosn = chaosn 

    card_fact = {
        "is_positive": nice[is_positive],
        "is_inexpected": nice[is_inexpected],
        "chaos": chaos[chaosn//20]
    }

    return card_fact

def card_phobia():
    phobia = match.randint(0, 100)
    is_nice = match.randint(0, 1)

    card_phobia = {
        "phobia": chaos[phobia//20],
        "is_nice": nice[is_nice]
    }

    return card_phobia

def card_ability():
    ability = match.randint(1, 9)
    is_nice = match.randint(0, 1)

    card_ability = {
        "ability": ability,
        'nice': nice[is_nice]
    }

    return card_ability

def inventory():
    is_job = match.randint(0, 1)
    inventory = match.randint(0, 100)
    is_nice = match.randint(0, 1)

    card_inventory = {
        "inventory": chaos[inventory//20],
        "is_job": nice[is_job],
        'is_nice': nice[is_nice]
    }

    return card_inventory


# Словари


AbilityType={
    1: "heal",
    2: "steal",
    3: "spoil",
    4: "gift",
    5: "spawn",
    6: "change_gender",
    7: "reveal",
    8: "swap_trait",
    9: "revive"
}

SkillType = {
    0: "новичок",
    1: "любитель",
    2: "опытный",
    3: "мастер",
    4: "эксперт",
    5: "профессионал"
}

rase = {
    0: "человек",
    1: "дворф",
    2: "гном",
    3: "орк",
    4: "эльф",
    5: "кошкочеловек",
    6: "кроликочеловек",
    7: "ящерочеловек",
    8: "вампир",
    9: "оборотень",
    10: "зомби",
    11: "робот",
    12: "инопланетянин",
    13: "Выбери сам абсурдную рассу 1 словом."}

chaos = {
    0: "логичный полностью",
    1: "странный, но есть в нашем мире",
    2: "очень редкие факты об людях, который стоит скрывать",
    3: "Смешной абсурд, который может случиться в реальной жизни",
    4: "Смешной абсурд, который вряд ли может случиться в реальной жизни",
    5: "Полностью смиешной абсурдный факт, который не может случиться в реальной жизни"
}

appearance = {
    0: "обычная",
    1: "необычная",
    2: "странная",
    3: "абсурдная",
    4: "смешная",
    5: "сексуальная",
}

heal = {
    0: "Страшная очень болезнь",
    1: "тяжелая болезнь",
    2: "легкая болезнь",
    3: "ранение",
    4: "легкое ранение",
    5: "здоров"
}

heal_appearance = {
    0: "здоровье связанно с внешностью",
    1: "здоровье не связанно с внешностью",
    2: "здоровье нельзя увидеть по внешности, но оно есть",
    3: "Идеально здоров, внешность красивая, тогда видно. Если нет, то оставь просто поле 'Идеально здоров'"
}

job = {
    0: "Лечит",
    1: "Ранит",
    2: "Грабит",
    3: "крутая работа без способности",
    4: "работает в сфере искусства",
    5: "абсурдная работа, вплоть до проституации",
}

nice = {
    0: "нет",
    1: "да"
}
