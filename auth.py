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

from models import PerfilPermissao
from database import get_db

# Dicionário de Módulos do Sistema
MODULOS_SISTEMA = {
    "mod_1": "1. Gestão de Vagas (Logística)",
    "mod_2": "2. Agendamento Manual (Suporte/Comercial)",
    "mod_3": "3. 📌 Central de Pendências de Agendamento",
    "mod_4": "4. Painel de Agenda (3 Dias)",
    "mod_5": "5. Importação de Excel (.xlsx / .xls)",
    "mod_6": "6. Gestão de Usuários"
}

def inicializar_permissoes_padrao():
    db = get_db()
    try:
        if db.query(PerfilPermissao).count() == 0:
            permissoes_iniciais = [
                # Admin (Acesso total)
                ("admin", "mod_1", True), ("admin", "mod_2", True), ("admin", "mod_3", True),
                ("admin", "mod_4", True), ("admin", "mod_5", True), ("admin", "mod_6", True),
                
                # Gestor Logística
                ("gestor_logistica", "mod_1", True), ("gestor_logistica", "mod_2", True), 
                ("gestor_logistica", "mod_3", True), ("gestor_logistica", "mod_4", True), 
                ("gestor_logistica", "mod_5", True), ("gestor_logistica", "mod_6", False),
                
                # Suporte
                ("suporte", "mod_1", False), ("suporte", "mod_2", True), 
                ("suporte", "mod_3", True), ("suporte", "mod_4", True), 
                ("suporte", "mod_5", False), ("suporte", "mod_6", False),
                
                # Comercial
                ("comercial", "mod_1", False), ("comercial", "mod_2", True), 
                ("comercial", "mod_3", True), ("comercial", "mod_4", True), 
                ("comercial", "mod_5", False), ("comercial", "mod_6", False),
            ]
            
            for perf, mod, perm in permissoes_iniciais:
                p = PerfilPermissao(perfil=perf, modulo_chave=mod, permitido=perm)
                db.add(p)
            db.commit()
    finally:
        db.close()
