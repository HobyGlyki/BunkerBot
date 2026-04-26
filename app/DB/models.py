from sqlalchemy import Column, Integer, String, Boolean, BigInteger, ForeignKey, Enum as SQLEnum, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import as_declarative
import enum

# --- Справочники ---

class GameStatus(enum.Enum):
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"

class CardType(enum.Enum):
    PROFESSION = "profession"
    appearance = "appearance"
    HEALTH = "health"
    INVENTORY = "inventory"
    BIOLOGY = "biology"
    ABILITY = "ability"
    PHOBIA = "phobia"
    HOBBY = "hobby"
    FACT = "fact"

class ActionEnum(enum.Enum):
    HEAL = "heal" #лечение
    STEAL = "steal" #  урон
    SPOIL = "spoil" # украсть
    GIFT = "gift" # получить
    SPAWN = "spawn" # заменить карточку игроку на случайную
    CHANGE_GENDER = "change_gender" #другой пол
    REVEAL = "reveal" #Раскрыть карту игрока
    SWAP_TRAIT = "swap_trait" #Поменяться карточкой с игроком
    REVIVE = "revive" #Вернуть игрока в бункер

# --- Таблицы ---

@as_declarative()
class AbstractModel:
    id = Column(Integer, primary_key=True, autoincrement=True)

class GameSession(AbstractModel):
    __tablename__ = 'games'
    
    status = Column(SQLEnum(GameStatus), default=GameStatus.WAITING)
    chaos_level = Column(Integer, default=0)
    disaster_description = Column(Text)
    bunker_capacity = Column(Integer)
    bunker_years = Column(Integer)
    bunker_features_json = Column(JSON)
    current_round = Column(Integer, default=1)
    current_phase = Column(String(50), default="narrative") # "reveal" (вскрытие), "action" (способности), "vote" (голосование)

class Player(AbstractModel):
    __tablename__ = 'players'
    
    game_id = Column(Integer, ForeignKey('games.id', ondelete="CASCADE"))
    tg_user_id = Column(BigInteger, unique=True, index=True)
    name = Column(String(100))
    is_dead = Column(Boolean, default=False)

class Card(AbstractModel):
    __tablename__ = 'cards'
    
   
    player_id = Column(Integer, ForeignKey('players.id', ondelete="CASCADE"), nullable=True)
    type = Column(SQLEnum(CardType))
    name = Column(String(100))
    power_level = Column(Integer, default=0)
    skill_level = Column(Integer, default=0)
    chaos_level = Column(Integer, default=0)
    interaction_type = Column(SQLEnum(ActionEnum), nullable=True)
    base_success_chance = Column(Integer, nullable=True)
    is_revealed = Column(Boolean, default=False)
    is_used = Column(Boolean, default=False)
    description = Column(String(255))