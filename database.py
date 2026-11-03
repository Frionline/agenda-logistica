import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

# Carrega a URL do banco a partir do Secrets do Streamlit Cloud
DATABASE_URL = st.secrets["postgres"]["url"]

# Ajusta conexões postgres:// legadas para postgresql:// exigidas pelas versões novas do SQLAlchemy
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

@st.cache_resource
def get_engine():
    return create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        pool_recycle=300
    )

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    return SessionLocal()

def init_db():
    import models
    Base.metadata.create_all(bind=engine)
