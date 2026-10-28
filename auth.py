import hashlib
from database import get_db
from models import Usuario

def hash_senha(senha: str) -> str:
    """Gera um hash SHA-256 simples e seguro para a senha."""
    return hashlib.sha256(senha.encode('utf-8')).hexdigest()

def autenticar_usuario(email, senha):
    """Autentica o usuário no banco de dados."""
    if not email or not senha:
        return None
        
    db = get_db()
    try:
        # Busca o usuário ignorando maiúsculas/minúsculas no e-mail
        email_limpo = email.strip().lower()
        usuarios = db.query(Usuario).all()
        
        for usr in usuarios:
            if usr.email and usr.email.strip().lower() == email_limpo:
                # Se o campo 'ativo' existir e for False, impede login
                if hasattr(usr, 'ativo') and usr.ativo is False:
                    return None
                    
                hash_digitado = hash_senha(senha)
                
                # Compara o hash digitado com o armazenado no banco
                if usr.senha_hash == hash_digitado or usr.senha_hash == senha:
                    return {
                        "id": usr.id,
                        "nome": usr.nome,
                        "email": usr.email,
                        "perfil": usr.perfil
                    }
        return None
    finally:
        db.close()

def criar_admin_padrao():
    """Garante a existência de ao menos um administrador ativo."""
    db = get_db()
    try:
        admin = db.query(Usuario).filter(Usuario.perfil == "admin").first()
        
        if not admin:
            novo_admin = Usuario(
                nome="Administrador",
                email="admin@frionline.com.br",
                senha_hash=hash_senha("admin123"),
                perfil="admin"
            )
            if hasattr(novo_admin, "ativo"):
                novo_admin.ativo = True
            db.add(novo_admin)
            db.commit()
        else:
            # Força a redefinição do e-mail, perfil e senha caso já exista
            admin.email = "admin@frionline.com.br"
            admin.senha_hash = hash_senha("admin123")
            if hasattr(admin, "ativo"):
                admin.ativo = True
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"Erro ao criar admin padrão: {e}")
    finally:
        db.close()
