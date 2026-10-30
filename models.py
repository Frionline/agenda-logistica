from sqlalchemy import Column, Integer, String, Date, Boolean, Text, DateTime
from datetime import datetime
from database import Base  # Importa a Base declarada em database.py

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    perfil = Column(String(50), nullable=False)  # admin, gestor_logistica, suporte, comercial
    ativo = Column(Boolean, default=True)

class DisponibilidadeVaga(Base):
    __tablename__ = "disponibilidade_vagas"

    id = Column(Integer, primary_key=True, index=True)
    data = Column(Date, index=True, nullable=False)
    cidade = Column(String(100), index=True, nullable=False)
    tipo_servico = Column(String(100), index=True, nullable=False)
    periodo = Column(String(50), nullable=False)  # Manhã, Livre, Tarde, Noite
    vagas_totais = Column(Integer, default=0)
    vagas_agendadas = Column(Integer, default=0)

class Agendamento(Base):
    __tablename__ = "agendamentos"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(String(100), index=True, nullable=False)
    id_cliente = Column(String(50), nullable=True)
    id_contrato = Column(String(50), nullable=True)
    cidade = Column(String(100), nullable=False)
    tipo_servico = Column(String(100), nullable=False)
    data_agendamento = Column(Date, index=True, nullable=False)
    periodo = Column(String(50), nullable=False)
    observacoes = Column(Text, nullable=True)
    status = Column(String(50), default="Agendado")
    agendado_por = Column(String(100), nullable=True)
    criador_excel = Column(String(100), nullable=True)
    nome_cliente = Column(String(200), nullable=True)
    rua = Column(String(200), nullable=True)
    bairro = Column(String(100), nullable=True)
    categoria_4 = Column(String(100), nullable=True)
    dados_completos = Column(Boolean, default=False)
    data_criacao = Column(DateTime, default=datetime.utcnow)

class ProtocoloPendente(Base):
    __tablename__ = "protocolos_pendentes"

    id = Column(Integer, primary_key=True, index=True)
    protocolo = Column(String(100), index=True, nullable=False)
    id_cliente = Column(String(50), nullable=True)
    id_contrato = Column(String(50), nullable=True)
    nome_cliente = Column(String(200), nullable=True)
    cidade = Column(String(100), nullable=True)
    tipo_servico = Column(String(100), nullable=True)
    rua = Column(String(200), nullable=True)
    bairro = Column(String(100), nullable=True)
    categoria_4 = Column(String(100), nullable=True)
    agendado_por = Column(String(100), nullable=True)
    criador_excel = Column(String(100), nullable=True)
    data_referencia = Column(Date, nullable=True)
    status = Column(String(50), default="Pendente")

class BloqueioAgenda(Base):
    __tablename__ = "bloqueios_agenda"

    id = Column(Integer, primary_key=True, index=True)
    data_inicio = Column(Date, nullable=False)
    data_fim = Column(Date, nullable=False)
    ativo = Column(Boolean, default=True)
    criado_por = Column(String(100), nullable=True)
