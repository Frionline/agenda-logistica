from models import PerfilPermissao, Base
from database import get_db, engine

MODULOS_SISTEMA = {
    "mod_1": "1. Gestão de Vagas (Logística)",
    "mod_2": "2. Agendamento Manual (Suporte/Comercial)",
    "mod_3": "3. 📌 Central de Pendências de Agendamento",
    "mod_4": "4. Painel de Agenda (3 Dias)",
    "mod_5": "5. Importação de Excel (.xlsx / .xls)",
    "mod_6": "6. Gestão de Usuários"
}

def inicializar_permissoes_padrao():
    # Força a criação da tabela no banco se ela não existir
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
