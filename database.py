import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

# Lê a URL configurada no Secrets do Streamlit Cloud
DATABASE_URL = st.secrets["postgres"]["url"]

@st.cache_resource
def get_engine():
    return create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Reconecta automaticamente se a conexão com o Neon cair por inatividade
        pool_size=5,
        max_overflow=10
    )

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@st.cache_resource
def init_db():
    import models
    # Cria as tabelas necessárias e inicializa o schema
    Base.metadata.create_all(bind=engine)

def get_db():
    return SessionLocal()
