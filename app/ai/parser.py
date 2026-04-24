from app.ai.schemas import CardsBatchResponse, CharacterDescriptionResponse
import json

def parse(ai_response: dict) -> CharacterDescriptionResponse:
    # Преобразуем словарь в объект Pydantic
    return CardsBatchResponse(**ai_response)

def parse_ai_response(ai_response_dict: str) -> CharacterDescriptionResponse:
    ai_response = json.loads(ai_response_dict)
    character_description = parse(ai_response)
    return character_description

def parse_random_response(ai_response_str: str) -> CardsBatchResponse:
    # 1. Превращаем строку JSON в настоящий список Python
    try:
        data_list = json.loads(ai_response_str)
        # 2. Передаем этот список в поле cards нашей модели
        return CardsBatchResponse(cards=data_list)
    except Exception as e:
        print(f"Ошибка парсинга: {e}")
        return CardsBatchResponse(cards=[])