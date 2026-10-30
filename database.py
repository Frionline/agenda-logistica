import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

DATABASE_URL = st.secrets["postgres"]["url"]

@st.cache_resource
def get_engine():
    return create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    import models
    # Garante o registro dos modelos ORM
    Base.metadata.create_all(bind=engine)

def get_db():
    return SessionLocal()
