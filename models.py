from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Usuario(Base):
    __tablename__ = 'usuarios'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    senha_hash = Column(String(255), nullable=False)
    perfil = Column(String(30), nullable=False)  # 'admin', 'gestor_logistica', 'suporte'
    ativo = Column(Boolean, default=True)
    ultimo_login = Column(DateTime, nullable=True)


class DisponibilidadeVaga(Base):
    __tablename__ = 'disponibilidade_vagas'

    id = Column(Integer, primary_key=True, autoincrement=True)
    data = Column(Date, nullable=False, index=True)
    cidade = Column(String(100), nullable=False, index=True)
    tipo_servico = Column(String(100), nullable=False)
    periodo = Column(String(20), nullable=False)  # 'Manhã', 'Livre', 'Tarde', 'Noite'
    vagas_totais = Column(Integer, default=0, nullable=False)
    vagas_agendadas = Column(Integer, default=0, nullable=False)


class Agendamento(Base):
    __tablename__ = 'agendamentos'

    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(String(50), nullable=False, index=True)  # Protocolo / Contrato / Cliente
    id_cliente = Column(String(50), nullable=True)
    id_contrato = Column(String(50), nullable=True)
    cidade = Column(String(100), nullable=False)
    tipo_servico = Column(String(100), nullable=False)
    data_agendamento = Column(Date, nullable=False, index=True)
    periodo = Column(String(20), nullable=False)
    observacoes = Column(String(500), nullable=True)
    status = Column(String(20), default='Agendado')  # 'Agendado', 'Reagendado'

    # Dados preenchidos via Excel (.xlsx / .xls)
    nome_cliente = Column(String(150), nullable=True)
    rua = Column(String(200), nullable=True)
    bairro = Column(String(100), nullable=True)
    categoria_4 = Column(String(100), nullable=True)
    agendado_por = Column(String(100), nullable=True)     # Quem cadastrou/agendou no sistema
    criador_excel = Column(String(100), nullable=True)    # Nome vindo da coluna Criador (AK)
    dados_completos = Column(Boolean, default=False)

    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ProtocoloPendente(Base):
    __tablename__ = 'protocolos_pendentes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    protocolo = Column(String(50), nullable=False, index=True)
    id_cliente = Column(String(50), nullable=True)
    id_contrato = Column(String(50), nullable=True)
    nome_cliente = Column(String(150), nullable=True)
    cidade = Column(String(100), nullable=True)
    tipo_servico = Column(String(100), nullable=True)
    rua = Column(String(200), nullable=True)
    bairro = Column(String(100), nullable=True)
    categoria_4 = Column(String(100), nullable=True)
    agendado_por = Column(String(100), nullable=True)
    criador_excel = Column(String(100), nullable=True)    # Coluna Criador (AK)
    data_referencia = Column(Date, nullable=False, index=True)
    status = Column(String(20), default='Pendente')        # 'Pendente', 'Agendado'
    criado_em = Column(DateTime, default=datetime.utcnow)

from sqlalchemy import Column, Integer, String, Date, Boolean
from database import Base

class BloqueioAgenda(Base):
    __tablename__ = "bloqueios_agenda"

    id = Column(Integer, primary_key=True, index=True)
    data_inicio = Column(Date, nullable=False)
    data_fim = Column(Date, nullable=False)
    ativo = Column(Boolean, default=True)
    criado_por = Column(String, nullable=True)
