import bcrypt
import streamlit as st
from datetime import datetime
from database import get_db
from models import Usuario

def hash_senha(senha: str) -> str:
    """Gera o hash seguro da senha."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(senha.encode('utf-8'), salt).decode('utf-8')

def verificar_senha(senha: str, senha_hash: str) -> bool:
    """Verifica se a senha digitada corresponde ao hash."""
    return bcrypt.checkpw(senha.encode('utf-8'), senha_hash.encode('utf-8'))

def autenticar_usuario(email: str, senha: str):
    """Valida o e-mail e senha no banco de dados Neon."""
    db = get_db()
    try:
        usuario = db.query(Usuario).filter(Usuario.email == email.strip().lower(), Usuario.ativo == True).first()
        if usuario and verificar_senha(senha, usuario.senha_hash):
            usuario.ultimo_login = datetime.utcnow()
            db.commit()
            
            # Extrai os dados em um dicionário antes de fechar a sessão
            dados_usuario = {
                "id": usuario.id,
                "nome": usuario.nome,
                "email": usuario.email,
                "perfil": usuario.perfil
            }
            return dados_usuario
        return None
    finally:
        db.close()

def criar_admin_padrao():
    """Cria um usuário administrador inicial caso a tabela esteja vazia."""
    db = get_db()
    try:
        if db.query(Usuario).count() == 0:
            admin = Usuario(
                nome="Administrador",
                email="admin@empresa.com",
                senha_hash=hash_senha("admin123"),
                perfil="admin",
                ativo=True
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()
