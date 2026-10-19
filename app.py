import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from database import init_db, get_db
from models import Usuario, DisponibilidadeVaga, Agendamento
from auth import autenticar_usuario, criar_admin_padrao, hash_senha

st.set_page_config(page_title="Sistema de Agendamento - Logística", layout="wide")

init_db()
criar_admin_padrao()

# Lista de Cidades e Serviços Padronizados
CIDADES = [
    "Nova Friburgo", "Lumiar", "Bom Jardim", "Duas Barras", "Cordeiro",
    "Cantagalo", "Macuco", "Trajano", "Madalena", "São Fidelis",
    "Itaocara", "Cardoso Moreira", "Cambuci", "Italva"
]

SERVICOS = [
    "Reparo", "Instalação", "Mudança de Endereço", "Upgrade", "Alteração de Ponto"
]

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
                st.session_state.usuario = usr
                st.success(f"Bem-vindo(a), {usr['nome']}!")
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
    
    opcoes_menu = []
    if usr["perfil"] in ["admin", "gestor_logistica"]:
        opcoes_menu.append("1. Gestão de Vagas (Logística)")
    if usr["perfil"] in ["admin", "suporte"]:
        opcoes_menu.append("2. Agendamento (Suporte)")
    if usr["perfil"] in ["admin", "gestor_logistica", "suporte"]:
        opcoes_menu.append("3. Painel de Agenda (3 Dias)")
    if usr["perfil"] in ["admin", "gestor_logistica"]:
        opcoes_menu.append("4. Importação de CSV")
    if usr["perfil"] == "admin":
        opcoes_menu.append("5. Gestão de Usuários")

    menu_selecionado = st.sidebar.radio("Navegação", opcoes_menu)

    # -------------------------------------------------------------------------
    # MÓDULO 1: GESTÃO DE VAGAS (LOGÍSTICA)
    # -------------------------------------------------------------------------
    if menu_selecionado == "1. Gestão de Vagas (Logística)":
        st.title("📅 Gestão de Disponibilidade de Vagas")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            cidade_sel = st.selectbox("Cidade", CIDADES)
        with col2:
            servico_sel = st.selectbox("Tipo de Serviço", SERVICOS)
        with col3:
            data_sel = st.date_input("Data do Serviço", value=date.today(), format="DD/MM/YYYY")

        st.markdown("### Configuração de Vagas por Período")
        db = get_db()
        try:
            periodos = ["Manhã", "Livre", "Tarde", "Noite"]
            vagas_input = {}
            
            col_m, col_l, col_t, col_n = st.columns(4)
            cols = [col_m, col_l, col_t, col_n]
            
            for i, p in enumerate(periodos):
                registro = db.query(DisponibilidadeVaga).filter_by(
                    data=data_sel, cidade=cidade_sel, tipo_servico=servico_sel, periodo=p
                ).first()
                
                agendadas_reais = db.query(Agendamento).filter_by(
                    data_agendamento=data_sel, cidade=cidade_sel, tipo_servico=servico_sel, periodo=p
                ).count()
                
                v_atual = registro.vagas_totais if registro else 0
                
                with cols[i]:
                    st.metric(f"Período: {p}", f"Agendadas: {agendadas_reais}")
                    vagas_input[p] = st.number_input(f"Total Vagas - {p}", min_value=agendadas_reais, value=max(v_atual, agendadas_reais), step=1)

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
                agendamento_existente = db.query(Agendamento).filter_by(cliente_id=cliente_id.strip()).first()
                
                if agendamento_existente:
                    st.warning(f"⚠️ Cliente já possui agendamento para {agendamento_existente.data_agendamento.strftime('%d/%m/%Y')} no período da {agendamento_existente.periodo}. Modo: REAGENDAMENTO.")
                
                c1, c2 = st.columns(2)
                with c1:
                    idx_cid = CIDADES.index(agendamento_existente.cidade) if (agendamento_existente and agendamento_existente.cidade in CIDADES) else 0
                    cidade_ag = st.selectbox("Cidade do Atendimento", CIDADES, index=idx_cid)
                with c2:
                    idx_serv = SERVICOS.index(agendamento_existente.tipo_servico) if (agendamento_existente and agendamento_existente.tipo_servico in SERVICOS) else 0
                    servico_ag = st.selectbox("Tipo de Serviço", SERVICOS, index=idx_serv)
                
                vagas_cadastradas = db.query(DisponibilidadeVaga).filter(
                    DisponibilidadeVaga.cidade == cidade_ag,
                    DisponibilidadeVaga.tipo_servico == servico_ag,
                    DisponibilidadeVaga.data >= date.today()
                ).all()
                
                vagas_disponiveis = []
                for v in vagas_cadastradas:
                    agendadas = db.query(Agendamento).filter_by(
                        data_agendamento=v.data, cidade=cidade_ag, tipo_servico=servico_ag, periodo=v.periodo
                    ).count()
                    
                    if agendamento_existente and agendamento_existente.data_agendamento == v.data and agendamento_existente.periodo == v.periodo:
                        agendadas -= 1
                        
                    if (v.vagas_totais - agendadas) > 0:
                        vagas_disponiveis.append(v)
                
                if not vagas_disponiveis:
                    st.error("Não existem vagas disponíveis para esta cidade e serviço no momento.")
                else:
                    opcoes_datas = sorted(list(set([v.data for v in vagas_disponiveis])))
                    data_escolhida = st.selectbox("Selecione a Data Disponível", opcoes_datas, format_func=lambda d: d.strftime("%d/%m/%Y"))
                    
                    periodos_disponiveis = [v for v in vagas_disponiveis if v.data == data_escolhida]
                    
                    periodo_escolhido = st.selectbox(
                        "Selecione o Período",
                        [p.periodo for p in periodos_disponiveis],
                        format_func=lambda p: f"{p}"
                    )
                    
                    obs = st.text_area("Observações (ex: Primeira da manhã)", value=agendamento_existente.observacoes if agendamento_existente else "")
                    
                    if st.button("Confirmar Agendamento"):
                        if agendamento_existente:
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

                        db.commit()
                        st.success("Agendamento realizado com sucesso!")
            finally:
                db.close()

    # -------------------------------------------------------------------------
    # MÓDULO 3: PAINEL DE AGENDA (VISUALIZAÇÃO 3 DIAS + RELATÓRIO)
    # -------------------------------------------------------------------------
    elif menu_selecionado == "3. Painel de Agenda (3 Dias)":
        st.title("📊 Painel da Agenda de Serviços")
        
        tab_painel, tab_detalhes = st.tabs(["🗓️ Visão 3 Dias (Grade)", "📋 Lista Detalhada de O.S."])
        
        # --- TAB 1: PAINEL EM GRADE (ESTILO PLANILHA COM LISTA DE CLIENTES) ---
        with tab_painel:
            col_c, col_s, col_d = st.columns(3)
            with col_c:
                cid_painel = st.selectbox("Selecione a Cidade", CIDADES)
            with col_s:
                serv_painel = st.selectbox("Selecione o Tipo de Serviço", SERVICOS)
            with col_d:
                data_inicio = st.date_input("Data Inicial", value=date.today(), format="DD/MM/YYYY")
                
            st.markdown("---")
            
            db = get_db()
            try:
                periodos = ["Manhã", "Livre", "Tarde", "Noite"]
                
                for i in range(3):
                    dia_atual = data_inicio + timedelta(days=i)
                    st.subheader(f"📅 Dia {dia_atual.strftime('%d/%m/%Y')} ({dia_atual.strftime('%A')})")
                    
                    disp_row = []
                    agend_row = []
                    
                    for p in periodos:
                        vaga = db.query(DisponibilidadeVaga).filter_by(
                            data=dia_atual, cidade=cid_painel, tipo_servico=serv_painel, periodo=p
                        ).first()
                        
                        agendadas_reais = db.query(Agendamento).filter_by(
                            data_agendamento=dia_atual, cidade=cid_painel, tipo_servico=serv_painel, periodo=p
                        ).count()
                        
                        totais = vaga.vagas_totais if vaga else 0
                        disponiveis = max(0, totais - agendadas_reais)
                        
                        disp_row.append(disponiveis)
                        agend_row.append(agendadas_reais)
                    
                    df_grade = pd.DataFrame({
                        "STATUS": ["DISPONÍVEIS", "AGENDADAS"],
                        "MANHÃ": [disp_row[0], agend_row[0]],
                        "LIVRE": [disp_row[1], agend_row[1]],
                        "TARDE": [disp_row[2], agend_row[2]],
                        "NOITE": [disp_row[3], agend_row[3]]
                    })
                    
                    st.dataframe(df_grade, use_container_width=True, hide_index=True)
                    
                    # Detalhamento retrátil dos clientes do dia
                    clientes_dia = db.query(Agendamento).filter_by(
                        data_agendamento=dia_atual, cidade=cid_painel, tipo_servico=serv_painel
                    ).all()
                    
                    with st.expander(f"🔍 Ver clientes agendados para {dia_atual.strftime('%d/%m/%Y')} ({len(clientes_dia)} cliente(s))"):
                        if clientes_dia:
                            listagem = []
                            for c in clientes_dia:
                                listagem.append({
                                    "ID Cliente": c.cliente_id,
                                    "Nome": c.nome_cliente if c.nome_cliente else "Aguardando CSV",
                                    "Período": c.periodo,
                                    "Observação": c.observacoes if c.observacoes else "-",
                                    "Status": c.status
                                })
                            st.dataframe(pd.DataFrame(listagem), use_container_width=True, hide_index=True)
                        else:
                            st.caption("Nenhum cliente agendado para esta cidade e serviço neste dia.")
                            
                    st.markdown("<br>", unsafe_allow_html=True)
            finally:
                db.close()
                
        # --- TAB 2: LISTA COMPLETA DE O.S. (CONSULTA E EXPORTAÇÃO) ---
        with tab_detalhes:
            st.subheader("Consulta e Download do Relatório")
            col_d1, col_c1 = st.columns(2)
            with col_d1:
                data_consulta = st.date_input("Data da Consulta", value=date.today(), format="DD/MM/YYYY")
            with col_c1:
                cidade_filtro = st.selectbox("Filtrar Cidade", ["Todas"] + CIDADES)
                
            db = get_db()
            try:
                query = db.query(Agendamento).filter(Agendamento.data_agendamento == data_consulta)
                if cidade_filtro != "Todas":
                    query = query.filter(Agendamento.cidade == cidade_filtro)
                    
                agendamentos = query.all()
                
                if not agendamentos:
                    st.info(f"Nenhum agendamento para {data_consulta.strftime('%d/%m/%Y')}.")
                else:
                    dados_tabela = []
                    for a in agendamentos:
                        dados_tabela.append({
                            "ID Cliente": a.cliente_id,
                            "Nome Cliente": a.nome_cliente if a.nome_cliente else "Pendente (CSV)",
                            "Cidade": a.cidade,
                            "Bairro": a.bairro if a.bairro else "-",
                            "Rua": a.rua if a.rua else "-",
                            "Serviço": a.tipo_servico,
                            "Período": a.periodo,
                            "Observações": a.observacoes if a.observacoes else "-",
                            "Categoria 4": a.categoria_4 if a.categoria_4 else "-",
                            "Status": a.status,
                            "Dados Completos": "Sim" if a.dados_completos else "Não"
                        })
                    
                    df_ag = pd.DataFrame(dados_tabela)
                    st.dataframe(df_ag, use_container_width=True)
                    
                    csv_data = df_ag.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Baixar Relatório em CSV",
                        data=csv_data,
                        file_name=f"agendamentos_{data_consulta.strftime('%Y_%m_%d')}.csv",
                        mime="text/csv"
                    )
            finally:
                db.close()

    # -------------------------------------------------------------------------
    # MÓDULO 4: IMPORTAÇÃO DE CSV
    # -------------------------------------------------------------------------
    elif menu_selecionado == "4. Importação de CSV":
        st.title("📥 Importação de CSV e Enriquecimento de Dados")
        
        arquivo_csv = st.file_uploader("Selecione o arquivo CSV", type=["csv"])
        data_referencia = st.date_input("Data de Referência dos Agendamentos", value=date.today(), format="DD/MM/YYYY")
        
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
    # MÓDULO 5: GESTÃO DE USUÁRIOS
    # -------------------------------------------------------------------------
    elif menu_selecionado == "5. Gestão de Usuários":
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
