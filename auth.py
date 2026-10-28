import bcrypt
from datetime import datetime
from database import get_db
from models import Usuario

def hash_senha(senha: str) -> str:
    """Gera o hash da senha utilizando bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(senha.encode('utf-8'), salt).decode('utf-8')

def verificar_senha(senha: str, senha_hash: str) -> bool:
    """Verifica se a senha em texto puro bate com o hash salvo."""
    try:
        return bcrypt.checkpw(senha.encode('utf-8'), senha_hash.encode('utf-8'))
    except Exception:
        return False

def autenticar_usuario(email: str, senha: str):
    """Verifica e-mail e senha no banco de dados e atualiza o último login."""
    db = get_db()
    try:
        usuario = db.query(Usuario).filter_by(email=email.strip().lower(), ativo=True).first()
        if usuario and verificar_senha(senha, usuario.senha_hash):
            usuario.ultimo_login = datetime.utcnow()
            db.commit()
            return {
                "id": usuario.id,
                "nome": usuario.nome,
                "email": usuario.email,
                "perfil": usuario.perfil
            }
        return None
    finally:
        db.close()

def criar_admin_padrao():
    """Cria um usuário administrador inicial caso não exista nenhum cadastrado."""
    db = get_db()
    try:
        admin_existente = db.query(Usuario).filter_by(email="admin@logistica.com").first()
        if not admin_existente:
            novo_admin = Usuario(
                nome="Administrador",
                email="admin@logistica.com",
                senha_hash=hash_senha("admin12345"),
                perfil="admin",
                ativo=True
            )
            db.add(novo_admin)
            db.commit()
    finally:
        db.close()
