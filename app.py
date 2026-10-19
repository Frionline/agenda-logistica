import streamlit as st
import pandas as pd
from datetime import date, datetime
from database import init_db, get_db
from models import Usuario, DisponibilidadeVaga, Agendamento
from auth import autenticar_usuario, criar_admin_padrao, hash_senha

# Configuração da Página
st.set_page_config(page_title="Sistema de Agendamento - Logística", layout="wide")

# Inicializa as tabelas no Neon e o Admin padrão
init_db()
criar_admin_padrao()

# Controle de Sessão
if "usuario" not in st.session_state:
    st.session_state.usuario = None

def fazer_logout():
    st.session_state.usuario = None
    st.rerun()

# -----------------------------------------------------------------------------
# TELA DE LOGIN
# -----------------------------------------------------------------------------
if st.session_state.usuario is None:
    st.title("🔐 Acesso ao Sistema")
    st.subheader("Atendimento e Gestão de Logística")
    
    with st.form("form_login"):
        email = st.text_input("E-mail de acesso")
        senha = st.text_input("Senha", type="password")
        btn_entrar = st.form_submit_button("Entrar")
        
        if btn_entrar:
            usr = autenticar_usuario(email, senha)
            if usr:
                st.session_state.usuario = {
                    "id": usr.id,
                    "nome": usr.nome,
                    "email": usr.email,
                    "perfil": usr.perfil
                }
                st.success(f"Bem-vindo(a), {usr.nome}!")
                st.rerun()
            else:
                st.error("E-mail ou senha incorretos (ou usuário inativo).")

else:
    usr = st.session_state.usuario
    st.sidebar.write(f"👤 **{usr['nome']}**")
    st.sidebar.caption(f"Perfil: {usr['perfil'].upper()}")
    if st.sidebar.button("Sair"):
        fazer_logout()
        
    st.sidebar.markdown("---")
    
    # Montagem Dinâmica do Menu de Acordo com o Perfil
    opcoes_menu = []
    if usr["perfil"] in ["admin", "gestor_logistica"]:
        opcoes_menu.append("1. Gestão de Vagas (Logística)")
    if usr["perfil"] in ["admin", "suporte"]:
        opcoes_menu.append("2. Agendamento (Suporte)")
    if usr["perfil"] in ["admin", "gestor_logistica"]:
        opcoes_menu.append("3. Importação de CSV")
    if usr["perfil"] == "admin":
        opcoes_menu.append("4. Gestão de Usuários")

    menu_selecionado = st.sidebar.radio("Navegação", opcoes_menu)

    # -------------------------------------------------------------------------
    # MÓDULO 1: GESTÃO DE VAGAS (LOGÍSTICA)
    # -------------------------------------------------------------------------
    if menu_selecionado == "1. Gestão de Vagas (Logística)":
        st.title("📅 Gestão de Disponibilidade de Vagas")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            cidade_sel = st.text_input("Cidade", value="Bom Jardim")
        with col2:
            servico_sel = st.selectbox("Tipo de Serviço", ["Reparo", "Mudança", "Instalação"])
        with col3:
            data_sel = st.date_input("Data do Serviço", value=date.today())

        st.markdown("### Configuração de Vagas por Período")
        db = get_db()
        try:
            periodos = ["Manhã", "Livre", "Tarde", "Noite"]
            vagas_input = {}
            
            col_m, col_l, col_t, col_n = st.columns(4)
            cols = [col_m, col_l, col_t, col_n]
            
            for i, p in enumerate(periodos):
                # Busca vaga existente
                registro = db.query(DisponibilidadeVaga).filter_by(
                    data=data_sel, cidade=cidade_sel, tipo_servico=servico_sel, periodo=p
                ).first()
                
                v_atual = registro.vagas_totais if registro else 0
                v_agendadas = registro.vagas_agendadas if registro else 0
                
                with cols[i]:
                    st.metric(f"Período: {p}", f"Agendadas: {v_agendadas}")
                    vagas_input[p] = st.number_input(f"Total Vagas - {p}", min_value=v_agendadas, value=v_atual, step=1)

            if st.button("Salvar Disponibilidade"):
                for p, qtd in vagas_input.items():
                    registro = db.query(DisponibilidadeVaga).filter_by(
                        data=data_sel, cidade=cidade_sel, tipo_servico=servico_sel, periodo=p
                    ).first()
                    
                    if registro:
                        registro.vagas_totais = qtd
                    else:
                        novo_reg = DisponibilidadeVaga(
                            data=data_sel, cidade=cidade_sel, tipo_servico=servico_sel,
                            periodo=p, vagas_totais=qtd, vagas_agendadas=0
                        )
                        db.add(novo_reg)
                db.commit()
                st.success("Disponibilidade de vagas atualizada com sucesso!")
        finally:
            db.close()

    # -------------------------------------------------------------------------
    # MÓDULO 2: AGENDAMENTO PELO SUPORTE
    # -------------------------------------------------------------------------
    elif menu_selecionado == "2. Agendamento (Suporte)":
        st.title("🎧 Central de Agendamentos e Reagendamentos")
        
        cliente_id = st.text_input("ID do Cliente", help="Digite o ID para pesquisar agendamentos existentes")
        
        if cliente_id:
            db = get_db()
            try:
                # Verifica se o ID já tem agendamento cadastrado
                agendamento_existente = db.query(Agendamento).filter_by(cliente_id=cliente_id.strip()).first()
                
                if agendamento_existente:
                    st.warning(f"⚠️ Cliente já possui agendamento para {agendamento_existente.data_agendamento.strftime('%d/%m/%Y')} no período da {agendamento_existente.periodo}. Modo: REAGENDAMENTO.")
                
                c1, c2 = st.columns(2)
                with c1:
                    cidade_ag = st.text_input("Cidade do Atendimento", value=agendamento_existente.cidade if agendamento_existente else "Bom Jardim")
                with c2:
                    servico_ag = st.selectbox("Tipo de Serviço", ["Reparo", "Mudança", "Instalação"], index=0)
                
                # Buscar datas com vagas disponíveis
                vagas_disponiveis = db.query(DisponibilidadeVaga).filter(
                    DisponibilidadeVaga.cidade == cidade_ag,
                    DisponibilidadeVaga.tipo_servico == servico_ag,
                    (DisponibilidadeVaga.vagas_totais - DisponibilidadeVaga.vagas_agendadas) > 0
                ).all()
                
                if not vagas_disponiveis:
                    st.error("Não existem vagas disponíveis para esta cidade e serviço no momento.")
                else:
                    opcoes_datas = sorted(list(set([v.data for v in vagas_disponiveis])))
                    data_escolhida = st.selectbox("Selecione a Data Disponível", opcoes_datas, format_func=lambda d: d.strftime("%d/%m/%Y"))
                    
                    # Filtra períodos com vagas na data escolhida
                    periodos_disponiveis = db.query(DisponibilidadeVaga).filter(
                        DisponibilidadeVaga.cidade == cidade_ag,
                        DisponibilidadeVaga.tipo_servico == servico_ag,
                        DisponibilidadeVaga.data == data_escolhida,
                        (DisponibilidadeVaga.vagas_totais - DisponibilidadeVaga.vagas_agendadas) > 0
                    ).all()
                    
                    periodo_escolhido = st.selectbox(
                        "Selecione o Período",
                        [p.periodo for p in periodos_disponiveis],
                        format_func=lambda p: f"{p} (Vagas restantes: {[v.vagas_totais - v.vagas_agendadas for v in periodos_disponiveis if v.periodo == p][0]})"
                    )
                    
                    obs = st.text_area("Observações (ex: Primeira da manhã)", value=agendamento_existente.observacoes if agendamento_existente else "")
                    
                    if st.button("Confirmar Agendamento"):
                        # Trata liberação da vaga antiga caso seja reagendamento
                        if agendamento_existente:
                            vaga_antiga = db.query(DisponibilidadeVaga).filter_by(
                                data=agendamento_existente.data_agendamento,
                                cidade=agendamento_existente.cidade,
                                tipo_servico=agendamento_existente.tipo_servico,
                                periodo=agendamento_existente.periodo
                            ).first()
                            if vaga_antiga and vaga_antiga.vagas_agendadas > 0:
                                vaga_antiga.vagas_agendadas -= 1
                            
                            agendamento_existente.cidade = cidade_ag
                            agendamento_existente.tipo_servico = servico_ag
                            agendamento_existente.data_agendamento = data_escolhida
                            agendamento_existente.periodo = periodo_escolhido
                            agendamento_existente.observacoes = obs
                            agendamento_existente.status = "Reagendado"
                        else:
                            novo_ag = Agendamento(
                                cliente_id=cliente_id.strip(),
                                cidade=cidade_ag,
                                tipo_servico=servico_ag,
                                data_agendamento=data_escolhida,
                                periodo=periodo_escolhido,
                                observacoes=obs,
                                status="Agendado"
                            )
                            db.add(novo_ag)
                        
                        # Consome a nova vaga
                        vaga_nova = db.query(DisponibilidadeVaga).filter_by(
                            data=data_escolhida, cidade=cidade_ag, tipo_servico=servico_ag, periodo=periodo_escolhido
                        ).first()
                        if vaga_nova:
                            vaga_nova.vagas_agendadas += 1

                        db.commit()
                        st.success("Agendamento realizado com sucesso!")
            finally:
                db.close()

    # -------------------------------------------------------------------------
    # MÓDULO 3: IMPORTAÇÃO DE CSV
    # -------------------------------------------------------------------------
    elif menu_selecionado == "3. Importação de CSV":
        st.title("📥 Importação de CSV e Enriquecimento de Dados")
        
        arquivo_csv = st.file_uploader("Selecione o arquivo CSV", type=["csv"])
        data_referencia = st.date_input("Data de Referência dos Agendamentos", value=date.today())
        
        if arquivo_csv and st.button("Processar e Atualizar Agendamentos"):
            df = pd.read_csv(arquivo_csv, dtype=str)
            st.write("Visualização do Arquivo Enviado:", df.head())
            
            db = get_db()
            atualizados = 0
            nao_encontrados = 0
            
            try:
                for _, row in df.iterrows():
                    c_id = str(row.get("cliente_id", "")).strip()
                    
                    if c_id:
                        ag = db.query(Agendamento).filter_by(cliente_id=c_id, data_agendamento=data_referencia).first()
                        if ag:
                            ag.nome_cliente = row.get("nome_cliente", None)
                            ag.rua = row.get("rua", None)
                            ag.bairro = row.get("bairro", None)
                            ag.categoria_4 = row.get("categoria_4", None) if ag.tipo_servico == "Reparo" else None
                            ag.dados_completos = True
                            atualizados += 1
                        else:
                            nao_encontrados += 1
                
                db.commit()
                st.success(f"Processamento concluído! {atualizados} registros atualizados com sucesso.")
                if nao_encontrados > 0:
                    st.info(f"{nao_encontrados} IDs do CSV não possuíam agendamento cadastrado para a data {data_referencia.strftime('%d/%m/%Y')}.")
            finally:
                db.close()

    # -------------------------------------------------------------------------
    # MÓDULO ADMIN: GESTÃO DE USUÁRIOS
    # -------------------------------------------------------------------------
    elif menu_selecionado == "4. Gestão de Usuários":
        st.title("👤 Gestão de Usuários e Permissões")
        
        with st.form("form_novo_usuario"):
            st.subheader("Cadastrar Novo Colaborador")
            nome_u = st.text_input("Nome Completo")
            email_u = st.text_input("E-mail (Login)")
            senha_u = st.text_input("Senha Inicial", type="password")
            perfil_u = st.selectbox("Perfil de Acesso", ["suporte", "gestor_logistica", "admin"])
            
            if st.form_submit_button("Cadastrar Usuário"):
                if nome_u and email_u and senha_u:
                    db = get_db()
                    try:
                        existe = db.query(Usuario).filter_by(email=email_u.strip().lower()).first()
                        if existe:
                            st.error("Este e-mail já está cadastrado!")
                        else:
                            novo_u = Usuario(
                                nome=nome_u,
                                email=email_u.strip().lower(),
                                senha_hash=hash_senha(senha_u),
                                perfil=perfil_u,
                                ativo=True
                            )
                            db.add(novo_u)
                            db.commit()
                            st.success(f"Usuário {nome_u} cadastrado com sucesso!")
                    finally:
                        db.close()
                else:
                    st.warning("Preencha todos os campos obrigatórios.")
