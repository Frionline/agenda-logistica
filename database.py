import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

# Declaração central da Base do ORM (evita importação circular)
Base = declarative_base()

# Lê a URL do Neon configurada nos segredos do Streamlit Cloud
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

@st.cache_resource
def init_db():
    import models  # Importa os modelos para registrá-los no metadata antes do create_all
    Base.metadata.create_all(bind=engine)
    
    # Executado apenas uma vez ao iniciar a aplicação (evita gargalo de conexões)
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE agendamentos ADD COLUMN IF NOT EXISTS id_cliente VARCHAR(50);"))
        conn.execute(text("ALTER TABLE agendamentos ADD COLUMN IF NOT EXISTS id_contrato VARCHAR(50);"))
        conn.execute(text("ALTER TABLE agendamentos ADD COLUMN IF NOT EXISTS agendado_por VARCHAR(100);"))
        conn.execute(text("ALTER TABLE agendamentos ADD COLUMN IF NOT EXISTS criador_excel VARCHAR(100);"))
        
        conn.execute(text("ALTER TABLE protocolos_pendentes ADD COLUMN IF NOT EXISTS id_cliente VARCHAR(50);"))
        conn.execute(text("ALTER TABLE protocolos_pendentes ADD COLUMN IF NOT EXISTS id_contrato VARCHAR(50);"))
        conn.execute(text("ALTER TABLE protocolos_pendentes ADD COLUMN IF NOT EXISTS agendado_por VARCHAR(100);"))
        conn.execute(text("ALTER TABLE protocolos_pendentes ADD COLUMN IF NOT EXISTS criador_excel VARCHAR(100);"))
        conn.commit()

def get_db():
    return SessionLocal()
