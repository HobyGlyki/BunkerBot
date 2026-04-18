from respone import format_character_prompt
from parser import map_character_data, parse_random_response


strs= {'biology': {'gender': 'женщина', 'old': 781, 'race': 'орк'}, 'appearance': {'appearance': 'странная', 'is_nice': 'нет', 'mass': 135, 'height': 320}, 'health': {'heal': 'легкая болезнь', 'is_appearance': 'здоровье связанно с внешностью'}, 'job': {'job': 'Лечит', 'is_nice': 'Бесполезная', 'skill': 99, 'can_be_ability': 0, 'ability_type': 'None', 'ability ID': 10}, 'hobby': {'hobby': 'странная', 'is_nice': 'да', 'is_job': 'да'}, 'fact': {'is_positive': 'нет', 'is_inexpected': 'да', 'chaos': 'Полностью смиешной абсурдный факт, который не может случиться в реальной жизни'}, 'phobia': {'phobia': 'Смешной абсурд, который может случиться в реальной жизни', 'is_nice': 'нет'}, 'inventory_1': {'inventory': 'Смешной абсурд, который может случиться в реальной жизни', 'is_job': 'нет', 'is_nice': 'нет'}, 'inventory_2': {'inventory': 'очень редкие факты об людях, который стоит скрывать', 'is_job': 'да', 'is_nice': 'да'}, 'ability_1': {'ability name': 'получить или подарить предмет', 'is_chaotic': 'Полностью смиешной абсурдный факт, который не может случиться в реальной жизни', 'ability ID': 4}, 'ability_2': {'ability name': 'заменить карточку игроку', 'is_chaotic': 'Смешной абсурд, который вряд ли может случиться в реальной жизни', 'ability ID': 5}}

def ai_response(data: dict) -> str:
    character_description = map_character_data(data)
    prompt = format_character_prompt(character_description)
    data = parse_random_response(data)
    sysprompt = prompt[0]
    charprompt = prompt[1]

    return prompt, data


print(ai_response(strs))