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
    
    # Cria novas tabelas declaradas no models (incluindo bloqueios_agenda)
    Base.metadata.create_all(bind=engine)
    
    # Executa verificações e criações manuais de colunas/tabelas caso faltem
    with engine.connect() as conn:
        # Garante a criação da tabela de bloqueio se não tiver sido criada
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS bloqueios_agenda (
                id SERIAL PRIMARY KEY,
                data_inicio DATE NOT NULL,
                data_fim DATE NOT NULL,
                ativo BOOLEAN DEFAULT TRUE,
                criado_por VARCHAR(100)
            );
        """))
        
        # Migração das colunas de agendamentos
        conn.execute(text("ALTER TABLE agendamentos ADD COLUMN IF NOT EXISTS id_cliente VARCHAR(50);"))
        conn.execute(text("ALTER TABLE agendamentos ADD COLUMN IF NOT EXISTS id_contrato VARCHAR(50);"))
        conn.execute(text("ALTER TABLE agendamentos ADD COLUMN IF NOT EXISTS agendado_por VARCHAR(100);"))
        conn.execute(text("ALTER TABLE agendamentos ADD COLUMN IF NOT EXISTS criador_excel VARCHAR(100);"))
        
        # Migração das colunas de protocolos pendentes
        conn.execute(text("ALTER TABLE protocolos_pendentes ADD COLUMN IF NOT EXISTS id_cliente VARCHAR(50);"))
        conn.execute(text("ALTER TABLE protocolos_pendentes ADD COLUMN IF NOT EXISTS id_contrato VARCHAR(50);"))
        conn.execute(text("ALTER TABLE protocolos_pendentes ADD COLUMN IF NOT EXISTS agendado_por VARCHAR(100);"))
        conn.execute(text("ALTER TABLE protocolos_pendentes ADD COLUMN IF NOT EXISTS criador_excel VARCHAR(100);"))
        
        conn.commit()

def get_db():
    return SessionLocal()
