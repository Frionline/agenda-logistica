import bcrypt
import streamlit as st
from datetime import datetime
from database import get_db
from models import Usuario

def hash_senha(senha: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(senha.encode('utf-8'), salt).decode('utf-8')

def verificar_senha(senha: str, senha_hash: str) -> bool:
    return bcrypt.checkpw(senha.encode('utf-8'), senha_hash.encode('utf-8'))

def autenticar_usuario(email: str, senha: str):
    db = get_db()
    try:
        usuario = db.query(Usuario).filter(Usuario.email == email.strip().lower(), Usuario.ativo == True).first()
        if usuario and verificar_senha(senha, usuario.senha_hash):
            usuario.ultimo_login = datetime.utcnow()
            db.commit()
            return usuario
        return None
    finally:
        db.close()

def criar_admin_padrao():
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
