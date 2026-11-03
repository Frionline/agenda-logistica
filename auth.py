import streamlit as st
import hashlib
from database import get_db, engine
from models import Usuario, PerfilPermissao, Base

# Dicionário global de módulos do sistema para o controle dinâmico de permissões
MODULOS_SISTEMA = {
    "mod_1": "1. Gestão de Vagas (Logística)",
    "mod_2": "2. Agendamento Manual (Suporte/Comercial)",
    "mod_3": "3. 📌 Central de Pendências de Agendamento",
    "mod_4": "4. Painel de Agenda (3 Dias)",
    "mod_5": "5. Importação de Excel (.xlsx / .xls)",
    "mod_6": "6. Gestão de Usuários"
}

def hash_senha(senha):
    """Gera um hash SHA-256 para salvar senhas no banco com segurança."""
    return hashlib.sha256(senha.encode('utf-8')).hexdigest()

def autenticar_usuario(email, senha):
    """Verifica credenciais no banco de dados e retorna os dados do usuário se ativo."""
    db = get_db()
    try:
        senha_h = hash_senha(senha)
        usr = db.query(Usuario).filter_by(email=email.strip().lower(), ativo=True).first()
        if usr and usr.senha_hash == senha_h:
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
    """Garante a existência da conta administrador padrão no sistema."""
    # Garante que as tabelas existam
    Base.metadata.create_all(bind=engine)
    
    db = get_db()
    try:
        admin_email = "admin@frionline.com.br"
        admin_existente = db.query(Usuario).filter_by(email=admin_email).first()
        if not admin_existente:
            novo_admin = Usuario(
                nome="Administrador Frionline",
                email=admin_email,
                senha_hash=hash_senha("admin123"),
                perfil="admin",
                ativo=True
            )
            db.add(novo_admin)
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"Erro ao criar admin padrão: {e}")
    finally:
        db.close()

def inicializar_permissoes_padrao():
    """Cria a tabela de permissões e popula com as permissões padrão se estiver vazia."""
    # Força a criação física da tabela perfis_permissoes no banco Neon/PostgreSQL
    Base.metadata.create_all(bind=engine)
    
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
    except Exception as e:
        db.rollback()
        print(f"Erro ao inicializar permissões: {e}")
    finally:
        db.close()
