from schemas import CharacterData, CharacterDescriptionResponse
import json

def parse(ai_response: dict) -> CharacterDescriptionResponse:
    # Преобразуем словарь в объект Pydantic
    return CharacterData(**ai_response)

def parse_ai_response(ai_response_dict: str) -> CharacterDescriptionResponse:
    ai_response = json.loads(ai_response_dict)
    character_description = parse(ai_response)
    return character_description

def map_character_data(ai_response_dict: dict) -> dict:
    character_description = {
    "gender": ai_response_dict['biology']['gender'],
    "old": ai_response_dict['biology']['old'],
    "race": ai_response_dict['biology']['race'],
    "appearance_desc": ai_response_dict['appearance']['appearance'],
    "appearance_nice": ai_response_dict['appearance']['is_nice'],
    "mass": ai_response_dict['appearance']['mass'],
    "height": ai_response_dict['appearance']['height'],
    "heal_status": ai_response_dict['health']['heal'],
    "heal_appearance": ai_response_dict['health']['is_appearance'],
    "job_name": ai_response_dict['job']['job'],
    "job_nice": ai_response_dict['job']['is_nice'],
    "job_skill": ai_response_dict['job']['skill'],
    "hobby_name": ai_response_dict['hobby']['hobby'],
    "hobby_nice": ai_response_dict['hobby']['is_nice'],
    "hobby_is_job": ai_response_dict['hobby']['is_job'],
    "fact_positive": ai_response_dict['fact']['is_positive'],
    "fact_unexpected": ai_response_dict['fact']['is_inexpected'],
    "fact_chaos": ai_response_dict['fact']['chaos'],
    "phobia_chaos": ai_response_dict['phobia']['phobia'],
    "phobia_nice": ai_response_dict['phobia']['is_nice'],
    "inv1_chaos": ai_response_dict['inventory_1']['inventory'],
    "inv1_is_job": ai_response_dict['inventory_1']['is_job'],
    "inv1_nice": ai_response_dict['inventory_1']['is_nice'],
    "inv2_chaos": ai_response_dict['inventory_2']['inventory'],
    "inv2_is_job": ai_response_dict['inventory_2']['is_job'],
    "inv2_nice": ai_response_dict['inventory_2']['is_nice'],
    "abil1_type": ai_response_dict['ability_1']['ability name'],
    "abil1_chaos": ai_response_dict['ability_1']['is_chaotic'],
    "abil2_type": ai_response_dict['ability_2']['ability name'],
    "abil2_chaos": ai_response_dict['ability_2']['is_chaotic'],
}
    return character_description

def parse_random_response(ai_response_dict: dict) -> CharacterData:
    character_description =ai_response_dict
    return CharacterData(**character_description)