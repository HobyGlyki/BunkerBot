from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# для тестов в оперативной памяти
DATABASE_URL = "sqlite:///./bunker.db"

#DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
 