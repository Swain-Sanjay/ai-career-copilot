from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "mysql+pymysql://2GGrci4B4upeoCZ.root:LMyhBxuApQnhMTy7@gateway01.ap-southeast-1.prod.alicloud.tidbcloud.com:4000/test"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()