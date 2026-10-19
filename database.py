import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models import Base

# Lê a URL do Neon configurada no segredo do Streamlit Cloud
DATABASE_URL = st.secrets["postgres"]["url"]

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    # Cria tabelas que ainda não existem
    Base.metadata.create_all(bind=engine)
    
    # Atualiza a estrutura de tabelas existentes adicionando colunas novas (caso não existam)
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE agendamentos ADD COLUMN IF NOT EXISTS contato_1 VARCHAR(50);"))
        conn.execute(text("ALTER TABLE agendamentos ADD COLUMN IF NOT EXISTS contato_2 VARCHAR(50);"))
        conn.commit()

def get_db():
    db = SessionLocal()
    return db
