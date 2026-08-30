from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# По умолчанию — файловый SQLite рядом с приложением. Другую базу можно
# задать переменной DATABASE_URL, но никаких паролей в коде: если нужен
# внешний PostgreSQL, он приходит только из окружения.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/pricetracker.db")

# check_same_thread нужен только SQLite. Для остальных драйверов этот
# аргумент нелегален и уронил бы запуск, поэтому добавляем его выборочно.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
