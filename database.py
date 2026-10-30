import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

DATABASE_URL = st.secrets["postgres"]["url"]

@st.cache_resource
def get_engine():
    return create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10
    )

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    import models
    
    # Cria tabelas caso não existam
    Base.metadata.create_all(bind=engine)
    
    # Executa DDLs diretamente no PostgreSQL com autocommit para aplicar colunas pendentes
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        # Tabela Bloqueio Agenda (Cadeado)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS bloqueios_agenda (
                id SERIAL PRIMARY KEY,
                data_inicio DATE NOT NULL,
                data_fim DATE NOT NULL,
                ativo BOOLEAN DEFAULT TRUE,
                criado_por VARCHAR(100)
            );
        """))
        
        # Colunas na tabela 'agendamentos'
        conn.execute(text("ALTER TABLE agendamentos ADD COLUMN IF NOT EXISTS id_cliente VARCHAR(50);"))
        conn.execute(text("ALTER TABLE agendamentos ADD COLUMN IF NOT EXISTS id_contrato VARCHAR(50);"))
        conn.execute(text("ALTER TABLE agendamentos ADD COLUMN IF NOT EXISTS agendado_por VARCHAR(100);"))
        conn.execute(text("ALTER TABLE agendamentos ADD COLUMN IF NOT EXISTS criador_excel VARCHAR(100);"))
        conn.execute(text("ALTER TABLE agendamentos ADD COLUMN IF NOT EXISTS nome_cliente VARCHAR(200);"))
        conn.execute(text("ALTER TABLE agendamentos ADD COLUMN IF NOT EXISTS rua VARCHAR(200);"))
        conn.execute(text("ALTER TABLE agendamentos ADD COLUMN IF NOT EXISTS bairro VARCHAR(100);"))
        conn.execute(text("ALTER TABLE agendamentos ADD COLUMN IF NOT EXISTS categoria_4 VARCHAR(100);"))
        conn.execute(text("ALTER TABLE agendamentos ADD COLUMN IF NOT EXISTS dados_completos BOOLEAN DEFAULT FALSE;"))
        
        # Colunas na tabela 'protocolos_pendentes'
        conn.execute(text("ALTER TABLE protocolos_pendentes ADD COLUMN IF NOT EXISTS id_cliente VARCHAR(50);"))
        conn.execute(text("ALTER TABLE protocolos_pendentes ADD COLUMN IF NOT EXISTS id_contrato VARCHAR(50);"))
        conn.execute(text("ALTER TABLE protocolos_pendentes ADD COLUMN IF NOT EXISTS agendado_por VARCHAR(100);"))
        conn.execute(text("ALTER TABLE protocolos_pendentes ADD COLUMN IF NOT EXISTS criador_excel VARCHAR(100);"))
        conn.execute(text("ALTER TABLE protocolos_pendentes ADD COLUMN IF NOT EXISTS nome_cliente VARCHAR(200);"))
        conn.execute(text("ALTER TABLE protocolos_pendentes ADD COLUMN IF NOT EXISTS rua VARCHAR(200);"))
        conn.execute(text("ALTER TABLE protocolos_pendentes ADD COLUMN IF NOT EXISTS bairro VARCHAR(100);"))
        conn.execute(text("ALTER TABLE protocolos_pendentes ADD COLUMN IF NOT EXISTS categoria_4 VARCHAR(100);"))
        conn.execute(text("ALTER TABLE protocolos_pendentes ADD COLUMN IF NOT EXISTS data_referencia DATE;"))
        conn.execute(text("ALTER TABLE protocolos_pendentes ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'Pendente';"))

        # Colunas na tabela 'disponibilidade_vagas'
        conn.execute(text("ALTER TABLE disponibilidade_vagas ADD COLUMN IF NOT EXISTS vagas_agendadas INT DEFAULT 0;"))

        # Padronização/Unificação das cidades
        conn.execute(text("UPDATE agendamentos SET cidade = 'Cordeiro e Cantagalo' WHERE LOWER(cidade) IN ('cordeiro', 'cantagalo');"))
        conn.execute(text("UPDATE agendamentos SET cidade = 'Trajano e Madalena' WHERE LOWER(cidade) IN ('trajano', 'madalena', 'santa maria madalena');"))
        conn.execute(text("UPDATE disponibilidade_vagas SET cidade = 'Cordeiro e Cantagalo' WHERE LOWER(cidade) IN ('cordeiro', 'cantagalo');"))
        conn.execute(text("UPDATE disponibilidade_vagas SET cidade = 'Trajano e Madalena' WHERE LOWER(cidade) IN ('trajano', 'madalena', 'santa maria madalena');"))

def get_db():
    return SessionLocal()
