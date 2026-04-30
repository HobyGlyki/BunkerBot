from operator import is_
import random as match   


genders = {0: "мужчина", 1: "женщина"}

AbilityType={
    1: "лечение здоровья",
    3: "исколечить здоровье",
    2: "украсть предмет",
    4: "получить или подарить предмет",
    5: "заменить карточку игроку на случайную",
    6: "изменение пола персонажа",
    7: "Раскрыть карту игрока",
    8: "Поменяться карточкой с игроком",
    9: "Использовать 2 голоса в голосовании",
    10: 'None'
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
    -4: "человек", -3: "человек", -2: "человек", -1: "человек", 0: "человек", 1: "Орк", 2: "гном", 3: "Дворф", 9: "эльф",
    5: "кошко-человек", 6: "кроликочеловек", 7: "ящеролюд",
    8: "вампир", 4: "оборотень", 10: "зомби", 11: "робот",
    12: "инопланетянин", 13: "живой скелет"
}

chaos = {
    0: "Скучная норма",
    1: "Странный заскок",
    2: "метерный абсурд",
    3: "Легкий абсурд",
    4: "Запущенный маразм",
    5: "Терминальное безумие"
}

appearance = {
    0: "Обычная внешность",
    1: "Атлетическое телосложение",
    2: "Рама 2 на 2",
    3: "дрыщь",
    4: "Ожирение",
    5: "Сексуальная внешность"
}


heal_location = {
    0: "Здоровым выглядит",
    1: "Голова (лицо, черепная коробка, скальп)",
    2: "Органы зрения (глаза, веки, зрачки)",
    3: "Ротовая полость (язык, зубы, дёсны)",
    4: "Слуховой аппарат (уши, перепонки)",
    5: "Мыслительный центр (мозг, извилины, кукуха)",
    6: "Верхние конечности (руки, локти, подмышки)",
    7: "Нижние конечности (ноги, коленные чашечки, пятки)",
    8: "Торс (грудная клетка, рёбра, область сердца)",
    9: "Жопа (ягодицы, копчик, филейная часть)",
    10: "Репродуктивный узел (гениталии)",
    11: "Конечности (пальцы рук, ног, когти)",
    12: "Внутренний мир (селезенка, аппендикс, почки)",
    13: "Пищеварительный тракт (желудок, кишечник, пупок)",
    14: "прочие органы (мизинец левой ноги, шишковидная железа, запасная печень)",
    15: "Абсурдные отростки (Гнилой хвост, Вторая жопа, щупальца, Чешуя)"
}

job = {
    0: "доктор",
    1: "Военный",
    2: "Инженер",
    3: "разнорабочий(придумай грязную проффесию)",
    5: "Проститутка",
    4: "абсурдная работа (придумай сам)",
}

nice = {0: "нет", 1: "да"}

# Основная Функция генерации карт

def generate_full_character():
    """
    Генерирует словарь с переменными сразу для 3-х карточек каждой из 11 категорий.
    Всего 33 заготовки.
    """
    data = {}
    
    for i in range(1, 4):
        # Biology
        bio = card_biology()
        data[f'gender{i}'] = bio['gender']
        data[f'race{i}'] = bio['race']
        data[f'old{i}'] = bio['old']
        
        # Appearance
        app = card_appearance()
        data[f'height{i}'] = app['height']
        data[f'appearance_desc{i}'] = app['appearance']
        
        # Health
        hlth = card_heal()
        data[f'heal_status{i}'] = hlth['heal']
        data[f'heal_appearance{i}'] = hlth['is_appearance']
        data[f'heal_level{i}'] = hlth['health_level'] # <-- Вытягиваем уровень
        
        # Job
        job_ = card_job()
        data[f'job_name{i}'] = job_['job']
        data[f'job_nice{i}'] = job_['is_nice']
        data[f'job_skill{i}'] = job_['skill']
        data[f'job_can_be_ability{i}'] = job_['can_be_ability']
        data[f'job_ability_ID{i}'] = job_['ability_ID']
        data[f'job_ability_type{i}'] = job_['ability_type']
        
        # Hobby
        hob = card_hobby()
        data[f'hobby_name{i}'] = hob['hobby']
        data[f'hobby_is_job{i}'] = hob['is_job']
        
        # Fact
        fct = card_fact()
        data[f'fact_chaos{i}'] = fct['chaos']
        data[f'fact_positive{i}'] = fct['is_positive']
        
        # Phobia
        phob = card_phobia()
        data[f'phobia_chaos{i}'] = phob['phobia']
        data[f'phobia_nice{i}'] = phob['is_nice']
        
        # Inventory 1 & 2
        inv1 = inventory()
        data[f'inv1_chaos{i}'] = inv1['inventory']
        data[f'inv1_nice{i}'] = inv1['is_nice']
        data[f'inv1_is_job{i}'] = inv1['is_job']

        inv2 = inventory()
        data[f'inv2_chaos{i}'] = inv2['inventory']
        data[f'inv2_nice{i}'] = inv2['is_nice']
        data[f'inv2_is_job{i}'] = inv2['is_job']
        
        # Ability 1 & 2
        abil1 = card_ability()
        data[f'abil1_type{i}'] = abil1['ability name']
        data[f'abil1_chaos{i}'] = abil1['is_chaotic']
        data[f'abil1_ID{i}'] = abil1['ability_ID']

        abil2 = card_ability()
        data[f'abil2_type{i}'] = abil2['ability name']
        data[f'abil2_chaos{i}'] = abil2['is_chaotic']
        data[f'abil2_ID{i}'] = abil2['ability_ID']
        
    return data
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

def card_biology():
    gender = match.randint(0, 1)

    rasen = match.randint(-13, 13)
    if rasen < 0: 
        rasen = 0
    if  rasen > 6:
        y = 20
        x = 200
    else:
        y = 10
        x = 75
    old = match.randint(y, x)
    
    card_biology = {
        "gender": genders[gender],
        "old": old,
        "race": rase[rasen]
    }

    return card_biology

def card_appearance():
    # Выбираем одно из 6 состояний внешности (0-5)
    appearancen = match.randint(0, 5)
    
    # Инициализируем переменные, которые зависят от типа
    height_cm = 180
    bmi = 22.0
    is_nice_val = 0

    if appearancen == 0:  # Обычная внешность
        height_cm = match.randint(100, 240)
        bmi = match.uniform(18.5, 26.0)
        is_nice_val = match.randint(0, 1) # Может быть симпатичным, может нет

    elif appearancen == 1:  # Атлетическое телосложение
        height_cm = match.randint(170, 200)
        bmi = match.uniform(22.5, 27.5)  # Плотный за счет мышц
        is_nice_val = 1

    elif appearancen == 2:  # Рама 2 на 2
        height_cm = match.randint(195, 260) # Очень высокий
        bmi = match.uniform(30.0, 45.0)     # Очень массивный
        is_nice_val = 1  # "Рама" — это звучит гордо

    elif appearancen == 3:  # Дрыщ
        height_cm = match.randint(165, 210)
        bmi = match.uniform(14.0, 18.0)     # Дефицит массы
        is_nice_val = 0

    elif appearancen == 4:  # Ожирение
        height_cm = match.randint(120, 185)
        bmi = match.uniform(35.0, 60.0)     # Значительный лишний вес
        is_nice_val = 0

    elif appearancen == 5:  # Сексуальная внешность
        height_cm = match.randint(165, 195)
        bmi = match.uniform(19.0, 24.5)     # Идеальные пропорции
        is_nice_val = 1

    # Математика расчета массы через ИМТ:
    # $$mass = BMI \cdot (height / 100)^2$$
    height_m = height_cm / 100
    mass = int(bmi * (height_m ** 2))

    # Формируем карточку
    card_appearance = {
        "appearance": appearance[appearancen],
        "is_nice": nice[is_nice_val],
        "mass": mass,
        "height": height_cm
    }

    return card_appearance

def card_heal():
    # Генерируем степень тяжести в процентах (от 10% до 95%)
    severity = match.randint(10, 95) 
    
    is_appearance = match.randint(0, 15)

    card_heal_dict = {
        "heal": severity, # Передаем число для ИИ
        "is_appearance": heal_location[is_appearance],
        "health_level": severity # Сохраняем число для записи в power_level
    }

    return card_heal_dict

def card_job():
    is_job_nice = match.randint(0, 1)
    job_val = match.randint(0, 100)
    skill = match.randint(0, 100)
    abil= 10
    if is_job_nice:
        js_job_nece = "полезная"
        if job_val//20 < 4:
            is_job_nice = True
            abil=job_val//20+1
        else:
            is_job_nice = False
    else: 
        js_job_nece = "Бесполезная"

    card_job = {
        "job": job[job_val//20],
        "is_nice": js_job_nece,
        "skill": skill,
        "can_be_ability": is_job_nice,
        "ability_type": AbilityType[abil],
        "ability_ID": abil
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
    chaos_level = match.randint(0, 5)

    card_ability = {
        "ability name": AbilityType[ability],
        'is_chaotic': chaos[chaos_level],
        'ability_ID': ability
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
