import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from database import init_db, get_db
from models import Usuario, DisponibilidadeVaga, Agendamento, ProtocoloPendente
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
        opcoes_menu.append("4. Importação de Excel (.xlsx)")
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
        
        db = get_db()
        try:
            # --- ÁREA DE PENDENTES DE AGENDAMENTO (ORIGEM: EXCEL) ---
            pendentes = db.query(ProtocoloPendente).filter_by(status="Pendente").all()
            if pendentes:
                with st.expander(f"📌 **Área de Pendentes de Agendamento ({len(pendentes)} protocolos aguardando)**", expanded=True):
                    st.info("Estes protocolos vieram do Excel importado e ainda não possuem vaga reservada. Escolha um protocolo para realizar o agendamento.")
                    
                    dados_p = []
                    for p in pendentes:
                        dados_p.append({
                            "Protocolo": p.protocolo,
                            "Cliente": p.nome_cliente if p.nome_cliente else "-",
                            "Cidade/Região": p.cidade if p.cidade else "-",
                            "Serviço": p.tipo_servico if p.tipo_servico else "-",
                            "Data Ref. Excel": p.data_referencia.strftime('%d/%m/%Y')
                        })
                    st.dataframe(pd.DataFrame(dados_p), use_container_width=True, hide_index=True)
            
            st.markdown("---")
            cliente_id = st.text_input("ID do Protocolo", help="Digite o número do protocolo para pesquisar agendamentos existentes")
            
            if cliente_id:
                agendamento_existente = db.query(Agendamento).filter_by(cliente_id=cliente_id.strip()).first()
                
                # Se for um protocolo pendente do Excel, busca os dados prévios salvos
                dados_pendente = db.query(ProtocoloPendente).filter_by(protocolo=cliente_id.strip(), status="Pendente").first()
                
                if agendamento_existente:
                    st.warning(f"⚠️ Este protocolo já possui agendamento para {agendamento_existente.data_agendamento.strftime('%d/%m/%Y')} no período da {agendamento_existente.periodo}. Modo: REAGENDAMENTO.")
                elif dados_pendente:
                    st.info(f"ℹ️ Protocolo localizado na lista de Pendentes de Agendamento. Cliente: {dados_pendente.nome_cliente or '-'}")
                
                c1, c2 = st.columns(2)
                with c1:
                    cid_inicial = agendamento_existente.cidade if agendamento_existente else (dados_pendente.cidade if dados_pendente and dados_pendente.cidade in CIDADES else CIDADES[0])
                    idx_cid = CIDADES.index(cid_inicial) if cid_inicial in CIDADES else 0
                    cidade_ag = st.selectbox("Cidade do Atendimento", CIDADES, index=idx_cid)
                with c2:
                    serv_inicial = agendamento_existente.tipo_servico if agendamento_existente else (dados_pendente.tipo_servico if dados_pendente and dados_pendente.tipo_servico in SERVICOS else SERVICOS[0])
                    idx_serv = SERVICOS.index(serv_inicial) if serv_inicial in SERVICOS else 0
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
                                status="Agendado",
                                nome_cliente=dados_pendente.nome_cliente if dados_pendente else None,
                                rua=dados_pendente.rua if dados_pendente else None,
                                bairro=dados_pendente.bairro if dados_pendente else None,
                                categoria_4=dados_pendente.categoria_4 if dados_pendente else None,
                                dados_completos=True if dados_pendente else False
                            )
                            db.add(novo_ag)
                            
                        # Se era um protocolo pendente do Excel, marca como concluído
                        if dados_pendente:
                            dados_pendente.status = "Agendado"

                        db.commit()
                        st.success("Agendamento realizado com sucesso!")
                        st.rerun()
        finally:
            db.close()

    # -------------------------------------------------------------------------
    # MÓDULO 3: PAINEL DE AGENDA (VISUALIZAÇÃO 3 DIAS + RELATÓRIO)
    # -------------------------------------------------------------------------
    elif menu_selecionado == "3. Painel de Agenda (3 Dias)":
        st.title("📊 Painel da Agenda de Serviços")
        
        tab_painel, tab_detalhes = st.tabs(["🗓️ Visão 3 Dias (Grade)", "📋 Lista Detalhada de O.S."])
        
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
                    
                    clientes_dia = db.query(Agendamento).filter_by(
                        data_agendamento=dia_atual, cidade=cid_painel, tipo_servico=serv_painel
                    ).all()
                    
                    with st.expander(f"🔍 Ver agendamentos para {dia_atual.strftime('%d/%m/%Y')} ({len(clientes_dia)} registro(s))"):
                        if clientes_dia:
                            listagem = []
                            for c in clientes_dia:
                                listagem.append({
                                    "Protocolo": c.cliente_id,
                                    "Cliente": c.nome_cliente if c.nome_cliente else "Aguardando Excel",
                                    "Período": c.periodo,
                                    "Observação": c.observacoes if c.observacoes else "-",
                                    "Status": c.status
                                })
                            st.dataframe(pd.DataFrame(listagem), use_container_width=True, hide_index=True)
                        else:
                            st.caption("Nenhum protocolo agendado para esta cidade e serviço neste dia.")
                            
                    st.markdown("<br>", unsafe_allow_html=True)
            finally:
                db.close()
                
        with tab_detalhes:
            st.subheader("Consulta e Download do Relatório Detalhado")
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
                            "Protocolo": a.cliente_id,
                            "Cliente": a.nome_cliente if a.nome_cliente else "Pendente (Excel)",
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
    # MÓDULO 4: IMPORTAÇÃO DE EXCEL (.XLSX)
    # -------------------------------------------------------------------------
    elif menu_selecionado == "4. Importação de Excel (.xlsx)":
        st.title("📥 Importação de Planilha Excel e Enriquecimento de Dados")
        
        arquivo_excel = st.file_uploader("Selecione o arquivo Excel (.xlsx ou .xls)", type=["xlsx", "xls"])
        data_referencia = st.date_input("Data de Referência dos Agendamentos", value=date.today(), format="DD/MM/YYYY")
        
        if arquivo_excel and st.button("Processar e Atualizar Agendamentos"):
            df = pd.read_excel(arquivo_excel, dtype=str)
            st.write("Visualização da Planilha Enviada:", df.head())
            
            db = get_db()
            atualizados = 0
            ignorados_recolhimento = 0
            protocolos_sem_agendamento = []
            
            try:
                for _, row in df.iterrows():
                    # 1. Ignorar se "Tipo geral" (Coluna O) for "recolhimento"
                    tipo_geral_val = None
                    if "Tipo geral" in df.columns:
                        tipo_geral_val = row.get("Tipo geral")
                    elif "Tipo Geral" in df.columns:
                        tipo_geral_val = row.get("Tipo Geral")
                    elif len(row) > 14:
                        tipo_geral_val = row.iloc[14]
                        
                    if tipo_geral_val and str(tipo_geral_val).strip().lower() == "recolhimento":
                        ignorados_recolhimento += 1
                        continue
                    
                    # 2. Identifica o Protocolo
                    c_id = str(row.get("id", row.get("protocolo", row.get("id_protocolo", row.get("cliente_id", ""))))).strip()
                    
                    if c_id and c_id.lower() != "nan":
                        ag = db.query(Agendamento).filter_by(cliente_id=c_id, data_agendamento=data_referencia).first()
                        
                        nome_c = row.get("cliente", row.get("nome_cliente", None))
                        rua_c = row.get("rua", None)
                        bairro_c = row.get("bairro", None)
                        cidade_c = row.get("cidade", row.get("regiao", None))
                        servico_c = row.get("servico", row.get("tipo_servico", None))
                        cat_4 = row.get("categoria_4", None)
                        
                        if ag:
                            ag.nome_cliente = nome_c
                            ag.rua = rua_c
                            ag.bairro = bairro_c
                            if ag.tipo_servico == "Reparo":
                                ag.categoria_4 = cat_4
                            ag.dados_completos = True
                            atualizados += 1
                        else:
                            # 3. Se não tem agendamento prévio no sistema, salva na área de Pendentes
                            existe_p = db.query(ProtocoloPendente).filter_by(protocolo=c_id, data_referencia=data_referencia).first()
                            if not existe_p:
                                novo_p = ProtocoloPendente(
                                    protocolo=c_id,
                                    nome_cliente=nome_c,
                                    cidade=cidade_c,
                                    tipo_servico=servico_c,
                                    rua=rua_c,
                                    bairro=bairro_c,
                                    categoria_4=cat_4,
                                    data_referencia=data_referencia,
                                    status="Pendente"
                                )
                                db.add(novo_p)
                            protocolos_sem_agendamento.append(f"{c_id} ({nome_c or 'Cliente sem nome'})")

                db.commit()
                
                st.success(f"✅ Processamento concluído! {atualizados} agendamentos atualizados com sucesso.")
                if ignorados_recolhimento > 0:
                    st.info(f"ℹ️ {ignorados_recolhimento} linha(s) foram ignoradas por serem do tipo 'recolhimento' (Coluna O).")
                
                # POPUP / ALERTA DE PROTOCOLOS SEM AGENDAMENTO PREVISTO
                if protocolos_sem_agendamento:
                    st.error(f"⚠️ **POPUP / ALERTA DE PROTOCOLOS SEM AGENDAMENTO PREVISTO**\n\nIdentificamos **{len(protocolos_sem_agendamento)} protocolo(s)** no Excel que não possuíam agendamento prévio no sistema para o dia {data_referencia.strftime('%d/%m/%Y')}.\n\nEles foram enviados para a **📌 Área de Pendentes de Agendamento** no menu do Suporte para que o colaborador faça o agendamento correto.\n\n**Lista de Protocolos:**\n" + "\n".join([f"- Protocolo {p}" for p in protocolos_sem_agendamento]))

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
