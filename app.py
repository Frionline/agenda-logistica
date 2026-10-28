import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from sqlalchemy import or_
import os
from database import init_db, get_db
from models import Usuario, DisponibilidadeVaga, Agendamento, ProtocoloPendente
from auth import autenticar_usuario, criar_admin_padrao, hash_senha
# Trecho temporário para redefinir a senha do admin
db_temp = get_db()
admin_temp = db_temp.query(Usuario).filter_by(email="admin@frionline.com.br").first()
if admin_temp:
    admin_temp.senha_hash = hash_senha("admin123")
    db_temp.commit()
db_temp.close()

st.set_page_config(
    page_title="Frionline - Agendamento Logístico",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

init_db()
criar_admin_padrao()

# -----------------------------------------------------------------------------
# ESTILIZAÇÃO CSS PERSONALIZADA (FRIONLINE - ORANGE TECH THEME)
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    /* Cores e Variáveis Frionline */
    :root {
        --primary-orange: #FF6600;
        --hover-orange: #E05500;
        --light-orange-bg: #FFF5EF;
        --dark-navy: #1E293B;
    }
    
    /* Estilização Geral de Botões */
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.25s ease-in-out !important;
        border: 1.5px solid #CBD5E1 !important;
        background-color: #FFFFFF !important;
    }
    
    .stButton > button:hover {
        border-color: #FF6600 !important;
        color: #FF6600 !important;
        box-shadow: 0px 4px 14px rgba(255, 102, 0, 0.25) !important;
        transform: translateY(-2px) !important;
    }
    
    /* Botões Primários */
    .stButton > button[kind="primary"], button[data-testid="stBaseButton-primary"] {
        background: linear-gradient(135deg, #FF6600 0%, #E05500 100%) !important;
        color: white !important;
        border: none !important;
        box-shadow: 0px 3px 8px rgba(255, 102, 0, 0.3) !important;
    }
    
    .stButton > button[kind="primary"]:hover, button[data-testid="stBaseButton-primary"]:hover {
        background: linear-gradient(135deg, #FF7711 0%, #F06000 100%) !important;
        border: 1.5px solid #FF8822 !important;
        color: white !important;
        box-shadow: 0px 6px 16px rgba(255, 102, 0, 0.45) !important;
        transform: translateY(-2px) !important;
    }
    
    /* Cards Customizados */
    .hero-container {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        padding: 2.2rem;
        border-radius: 14px;
        color: white;
        margin-bottom: 2rem;
        border-left: 6px solid #FF6600;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.25);
    }
    
    .info-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #FF6600;
        padding: 1.25rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
    }
    
    /* BARRA LATERAL (SIDEBAR) EM DARK MODE */
    section[data-testid="stSidebar"] {
        background-color: #1E293B !important;
        border-right: 1px solid #334155 !important;
    }
    
    section[data-testid="stSidebar"] * {
        color: #F1F5F9 !important;
    }
    
    section[data-testid="stSidebar"] .stRadio label p {
        color: #F1F5F9 !important;
        font-weight: 500 !important;
        font-size: 0.95rem !important;
    }

    section[data-testid="stSidebar"] .stButton > button {
        background-color: #0F172A !important;
        color: #F8FAFC !important;
        border: 1px solid #334155 !important;
    }

    section[data-testid="stSidebar"] .stButton > button:hover {
        border-color: #FF6600 !important;
        color: #FF6600 !important;
        background-color: #1E293B !important;
    }
    
    /* Badge Frionline */
    .frionline-badge {
        background-color: #FF6600;
        color: white !important;
        padding: 8px 20px;
        border-radius: 25px;
        font-size: 14px;
        font-weight: 700;
        letter-spacing: 1px;
        display: inline-block;
        box-shadow: 0px 4px 10px rgba(255, 102, 0, 0.3);
    }
    
    .badge-container {
        display: flex;
        align-items: center;
        justify-content: flex-start;
        padding-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Lista de Cidades e Serviços Padronizados
CIDADES = [
    "Nova Friburgo", "Lumiar", "Bom Jardim", "Duas Barras", "Cordeiro",
    "Cantagalo", "Macuco", "Trajano", "Madalena", "São Fidelis",
    "Itaocara", "Cardoso Moreira", "Cambuci", "Italva"
]

SERVICOS = [
    "Reparo", "Instalação", "Mudança de Endereço", "Upgrade", "Alteração de Ponto"
]

def limpar_str(val):
    if pd.isna(val) or val is None:
        return ""
    val_str = str(val).strip()
    if val_str.endswith(".0"):
        val_str = val_str[:-2]
    return val_str

def normalizar_servico(serv_str):
    if not serv_str or pd.isna(serv_str):
        return "Reparo"
    s = str(serv_str).strip()
    s_lower = s.lower()
    
    if "ponto" in s_lower:
        return "Alteração de Ponto"
    elif "mud" in s_lower or "endereço" in s_lower or "endereco" in s_lower:
        return "Mudança de Endereço"
    elif "instala" in s_lower or "ativa" in s_lower:
        return "Instalação"
    elif "reparo" in s_lower or "manuten" in s_lower:
        return "Reparo"
    elif "upgrade" in s_lower:
        return "Upgrade"
    return s

if "usuario" not in st.session_state:
    st.session_state.usuario = None

def fazer_logout():
    st.session_state.usuario = None
    if "menu_navegacao" in st.session_state:
        del st.session_state["menu_navegacao"]
    st.rerun()

# -----------------------------------------------------------------------------
# TELA DE LOGIN (DESIGN CORPORATIVO FRIONLINE)
# -----------------------------------------------------------------------------
if st.session_state.usuario is None:
    
    # Cabeçalho do App com Logo Ampliado e Badge Centralizado
    col_logo1, col_logo2 = st.columns([1.8, 2], vertical_alignment="center")
    with col_logo1:
        if os.path.exists("logo.png"):
            st.image("logo.png", width=420)
        elif os.path.exists("logo.jpg"):
            st.image("logo.jpg", width=420)
        else:
            st.markdown("<h1 style='color: #FF6600; font-size: 3.8rem; font-weight: 900; margin: 0; letter-spacing: -1px;'>FRIONLINE</h1>", unsafe_allow_html=True)
    with col_logo2:
        st.markdown("""
            <div class="badge-container">
                <span class="frionline-badge">SISTEMA CORPORATIVO FRIONLINE</span>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Hero Banner Principal com Emoji de Agenda 📅
    st.markdown("""
        <div class="hero-container">
            <h1 style="color: #FFFFFF; margin-bottom: 8px; font-size: 2.2rem; font-weight: 800;">
                📅 Central de Agendamentos & Operações Logísticas
            </h1>
            <p style="color: #CBD5E1; font-size: 1.05rem; margin-bottom: 0px; line-height: 1.5;">
                Sua plataforma unificada para controle de disponibilidade por cidade, agendamento inteligente de ordens de serviço e acompanhamento técnico em tempo real.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Layout de Login em 2 Colunas
    col_info, col_login = st.columns([1.1, 0.9], gap="large")

    with col_info:
        st.markdown("""
            <div class="info-card">
                <h3 style="color: #1E293B; margin-top: 0; font-size: 1.25rem;">📌 Acesso Restrito a Colaboradores</h3>
                <p style="color: #475569; line-height: 1.6; font-size: 0.98rem;">
                    Para agendar serviços, consultar vagas de logística ou processar planilhas pendentes, efetue seu login ao lado com sua conta corporativa.
                </p>
                <hr style="border: 0; border-top: 1px solid #E2E8F0; margin: 15px 0;">
                <ul style="color: #64748B; font-size: 0.92rem; padding-left: 18px; margin-bottom: 0;">
                    <li style="margin-bottom: 8px;"><b>Suporte & Comercial:</b> Agendamento manual e tratamento de pendências importadas.</li>
                    <li style="margin-bottom: 8px;"><b>Gestão Logística:</b> Configuração de vagas diárias por cidade e tipo de O.S.</li>
                    <li><b>Relatórios & Painéis:</b> Visão completa da agenda técnica dos próximos 3 dias.</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

    with col_login:
        st.markdown("<h3 style='color: #1E293B; margin-top: 0;'>🔐 Autenticação</h3>", unsafe_allow_html=True)
        with st.form("form_login"):
            email = st.text_input("E-mail de acesso", placeholder="seu.email@frionline.com.br")
            senha = st.text_input("Senha", type="password", placeholder="••••••••")
            btn_entrar = st.form_submit_button("Entrar no Sistema", type="primary", use_container_width=True)
            
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
    
    # Exibição de Logo na Barra Lateral
    if os.path.exists("logo.png"):
        st.sidebar.image("logo.png", use_column_width=True)
    elif os.path.exists("logo.jpg"):
        st.sidebar.image("logo.jpg", use_column_width=True)
    else:
        st.sidebar.markdown("<h2 style='color: #FF6600; font-size: 2.2rem; font-weight: 900; margin-bottom: 0;'>FRIONLINE</h2>", unsafe_allow_html=True)
        st.sidebar.caption("LOGÍSTICA & OPERAÇÕES")
        
    st.sidebar.markdown("---")
    st.sidebar.write(f"👤 **{usr['nome']}**")
    st.sidebar.caption(f"Perfil: {usr['perfil'].upper()}")
    if st.sidebar.button("🚪 Sair do Sistema", use_container_width=True):
        fazer_logout()
        
    st.sidebar.markdown("---")
    
    opcoes_menu = []
    if usr["perfil"] in ["admin", "gestor_logistica"]:
        opcoes_menu.append("1. Gestão de Vagas (Logística)")
    if usr["perfil"] in ["admin", "suporte", "comercial"]:
        opcoes_menu.append("2. Agendamento Manual (Suporte/Comercial)")
    if usr["perfil"] in ["admin", "gestor_logistica", "suporte", "comercial"]:
        opcoes_menu.append("3. 📌 Central de Pendências de Agendamento")
    if usr["perfil"] in ["admin", "gestor_logistica", "suporte", "comercial"]:
        opcoes_menu.append("4. Painel de Agenda (3 Dias)")
    if usr["perfil"] in ["admin", "gestor_logistica"]:
        opcoes_menu.append("5. Importação de Excel (.xlsx / .xls)")
    if usr["perfil"] == "admin":
        opcoes_menu.append("6. Gestão de Usuários")
    
    # Opção disponível para todos os colaboradores logados
    opcoes_menu.append("🔑 Alterar Minha Senha")

    # Garante que o estado do menu permaneça válido entre renderizações
    if "menu_navegacao" in st.session_state and st.session_state["menu_navegacao"] not in opcoes_menu:
        st.session_state["menu_navegacao"] = opcoes_menu[0]

    menu_selecionado = st.sidebar.radio("Navegação", opcoes_menu, key="menu_navegacao")

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

            if st.button("Salvar Disponibilidade", type="primary"):
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
    # MÓDULO 2: AGENDAMENTO MANUAL (SUPORTE / COMERCIAL)
    # -------------------------------------------------------------------------
    elif menu_selecionado == "2. Agendamento Manual (Suporte/Comercial)":
        st.title("🎧 Central de Agendamentos e Reagendamentos Manual")
        
        if "msg_sucesso_manual" in st.session_state:
            st.success(st.session_state.pop("msg_sucesso_manual"))
            
        if "input_proto_manual" not in st.session_state:
            st.session_state["input_proto_manual"] = ""

        db = get_db()
        try:
            cliente_id_input = st.text_input(
                "ID de Protocolo", 
                key="input_proto_manual", 
                help="Digite o número para pesquisar agendamentos existentes"
            )
            cliente_id = limpar_str(cliente_id_input)
            
            if cliente_id:
                todos_ag = db.query(Agendamento).filter(
                    or_(
                        Agendamento.cliente_id == cliente_id,
                        Agendamento.id_cliente == cliente_id,
                        Agendamento.id_contrato == cliente_id
                    )
                ).all()
                
                agendamento_existente = None
                if todos_ag:
                    agendamento_existente = todos_ag[-1]
                
                dados_pendente = db.query(ProtocoloPendente).filter(
                    (ProtocoloPendente.protocolo == cliente_id) |
                    (ProtocoloPendente.id_cliente == cliente_id) |
                    (ProtocoloPendente.id_contrato == cliente_id)
                ).first()
                
                eh_reagendamento = False
                if agendamento_existente and agendamento_existente.status in ["Agendado", "Reagendado"]:
                    eh_reagendamento = True
                    st.warning(f"⚠️ Este protocolo já possui agendamento para {agendamento_existente.data_agendamento.strftime('%d/%m/%Y')} no período da {agendamento_existente.periodo}. Modo: REAGENDAMENTO.")
                elif dados_pendente:
                    st.info(f"ℹ️ Protocolo localizado na lista de Pendentes. Cliente: {dados_pendente.nome_cliente or '-'}")
                else:
                    st.info("ℹ️ Novo agendamento manual (Protocolo não cadastrado anteriormente).")

                c1, c2 = st.columns(2)
                with c1:
                    opcoes_cidades = ["Selecione a cidade..."] + CIDADES
                    cidade_ag = st.selectbox("Cidade do Atendimento *", opcoes_cidades, index=0)
                with c2:
                    opcoes_servicos = ["Selecione o serviço..."] + SERVICOS
                    servico_ag = st.selectbox("Tipo de Serviço *", opcoes_servicos, index=0)
                
                cidade_valida = cidade_ag if cidade_ag in CIDADES else None
                servico_valido = servico_ag if servico_ag in SERVICOS else None

                if not cidade_valida or not servico_valido:
                    st.info("👆 Selecione a **Cidade do Atendimento** e o **Tipo de Serviço** para carregar as datas e vagas disponíveis.")
                else:
                    vagas_cadastradas = db.query(DisponibilidadeVaga).filter(
                        DisponibilidadeVaga.cidade == cidade_valida,
                        DisponibilidadeVaga.tipo_servico == servico_valido,
                        DisponibilidadeVaga.data >= date.today()
                    ).all()
                    
                    vagas_disponiveis = []
                    for v in vagas_cadastradas:
                        agendadas = db.query(Agendamento).filter_by(
                            data_agendamento=v.data, cidade=cidade_valida, tipo_servico=servico_valido, periodo=v.periodo
                        ).count()
                        
                        if eh_reagendamento and agendamento_existente.data_agendamento == v.data and agendamento_existente.periodo == v.periodo:
                            agendadas -= 1
                            
                        if (v.vagas_totais - agendadas) > 0:
                            vagas_disponiveis.append(v)
                    
                    if not vagas_disponiveis:
                        st.error("Não existem vagas disponíveis para esta cidade e serviço no momento.")
                    else:
                        opcoes_datas = sorted(list(set([v.data for v in vagas_disponiveis])))
                        
                        data_escolhida = st.selectbox(
                            "Selecione a Data Disponível *", 
                            [None] + opcoes_datas, 
                            format_func=lambda d: "Selecione a data..." if d is None else d.strftime("%d/%m/%Y"),
                            index=0
                        )
                        
                        if data_escolhida is None:
                            periodos_disponiveis = []
                        else:
                            periodos_disponiveis = [v.periodo for v in vagas_disponiveis if v.data == data_escolhida]
                        
                        periodo_escolhido = st.selectbox(
                            "Selecione o Período *",
                            [None] + periodos_disponiveis,
                            format_func=lambda p: "Selecione o período..." if p is None else f"{p}",
                            index=0
                        )
                        
                        obs = st.text_area("Observações (ex: Primeira da manhã)", value=agendamento_existente.observacoes if (agendamento_existente and eh_reagendamento) else "")
                        
                        if st.button("Confirmar Agendamento", type="primary"):
                            if not cidade_valida or not servico_valido or data_escolhida is None or periodo_escolhido is None:
                                st.error("⚠️ Preenchimento obrigatório! Por favor, selecione a Cidade, o Serviço, a Data e o Período antes de confirmar.")
                            else:
                                if eh_reagendamento and agendamento_existente:
                                    agendamento_existente.cidade = cidade_valida
                                    agendamento_existente.tipo_servico = servico_valido
                                    agendamento_existente.data_agendamento = data_escolhida
                                    agendamento_existente.periodo = periodo_escolhido
                                    agendamento_existente.observacoes = obs
                                    agendamento_existente.status = "Reagendado"
                                    agendamento_existente.agendado_por = usr["nome"]
                                else:
                                    novo_ag = Agendamento(
                                        cliente_id=cliente_id,
                                        cidade=cidade_valida,
                                        tipo_servico=servico_valido,
                                        data_agendamento=data_escolhida,
                                        periodo=periodo_escolhido,
                                        observacoes=obs,
                                        status="Agendado",
                                        agendado_por=usr["nome"],
                                        criador_excel=dados_pendente.criador_excel if (dados_pendente and getattr(dados_pendente, 'criador_excel', None)) else None,
                                        nome_cliente=dados_pendente.nome_cliente if dados_pendente else None,
                                        rua=dados_pendente.rua if dados_pendente else None,
                                        bairro=dados_pendente.bairro if dados_pendente else None,
                                        categoria_4=dados_pendente.categoria_4 if dados_pendente else None,
                                        dados_completos=True if dados_pendente else False
                                    )
                                    db.add(novo_ag)
                                    
                                if dados_pendente:
                                    dados_pendente.status = "Agendado"

                                db.commit()
                                st.session_state["msg_sucesso_manual"] = f"✅ Agendamento do protocolo {cliente_id} realizado com sucesso!"
                                st.session_state["input_proto_manual"] = ""
                                st.rerun()
        finally:
            db.close()

    # -------------------------------------------------------------------------
    # MÓDULO 3: CENTRAL DE PENDÊNCIAS DE AGENDAMENTO
    # -------------------------------------------------------------------------
    elif menu_selecionado == "3. 📌 Central de Pendências de Agendamento":
        st.title("📌 Central de Protocolos Pendentes de Agendamento")
        st.caption("Protocolos importados do Excel que ainda não possuem data/período agendados no sistema.")
        
        if "msg_sucesso_pendente" in st.session_state:
            st.success(st.session_state.pop("msg_sucesso_pendente"))
            
        db = get_db()
        try:
            pendentes = db.query(ProtocoloPendente).filter(
                or_(ProtocoloPendente.status == "Pendente", ProtocoloPendente.status == None, ProtocoloPendente.status == "")
            ).all()
            
            if not pendentes:
                st.info("ℹ️ Nenhum protocolo pendente encontrado no momento. Faça a importação da planilha no Módulo 5 para carregar os novos casos.")
            else:
                m1, m2, m3 = st.columns(3)
                m1.metric("Total Pendentes", f"{len(pendentes)} O.S.")
                
                cidades_p = set([p.cidade for p in pendentes if p.cidade])
                m2.metric("Cidades Envolvidas", f"{len(cidades_p)} cidades")
                
                servicos_p = set([p.tipo_servico for p in pendentes if p.tipo_servico])
                m3.metric("Tipos de Serviço", f"{len(servicos_p)} tipos")
                
                st.markdown("---")
                st.subheader("📋 Lista de Protocolos Aguardando Vaga")
                
                dados_p = []
                for p in pendentes:
                    dados_p.append({
                        "Protocolo": p.protocolo,
                        "ID Cliente": p.id_cliente or "-",
                        "ID Contrato": p.id_contrato or "-",
                        "Cliente": p.nome_cliente or "Sem nome",
                        "Cidade/Região": p.cidade or "-",
                        "Serviço": p.tipo_servico or "-",
                        "Endereço": f"{p.rua or '-'}, {p.bairro or '-'}",
                        "Criador (AK)": p.criador_excel or "-",
                        "Data Ref. Excel": p.data_referencia.strftime('%d/%m/%Y') if p.data_referencia else "-"
                    })
                
                st.dataframe(pd.DataFrame(dados_p), use_container_width=True)
                
                st.markdown("---")
                st.subheader("⚡ Agendar Protocolo Pendente em 1 Clique")
                
                opcoes_pendentes = {
                    f"Protocolo: {p.protocolo} | Cliente: {p.nome_cliente or 'Sem nome'} | {p.cidade or 'Cidade N/D'} ({p.tipo_servico or 'Serviço N/D'})": p
                    for p in pendentes
                }
                
                selecao = st.selectbox("Selecione o Protocolo que deseja agendar agora:", list(opcoes_pendentes.keys()))
                p_sel = opcoes_pendentes[selecao]
                
                with st.form("form_agendar_pendente"):
                    c_info1, c_info2 = st.columns(2)
                    with c_info1:
                        st.markdown(f"**Protocolo:** `{p_sel.protocolo}`")
                        st.markdown(f"**Cliente:** {p_sel.nome_cliente or '-'}")
                        st.markdown(f"**Endereço:** {p_sel.rua or '-'}, {p_sel.bairro or '-'}")
                    with c_info2:
                        st.markdown(f"**Criador (Coluna AK):** {p_sel.criador_excel or '-'}")
                        
                        cid_padrao = p_sel.cidade if (p_sel.cidade in CIDADES) else CIDADES[0]
                        idx_c = CIDADES.index(cid_padrao)
                        cidade_confirm = st.selectbox("Confirmar Cidade", CIDADES, index=idx_c)
                        
                        serv_norm = normalizar_servico(p_sel.tipo_servico)
                        opcoes_serv = list(SERVICOS)
                        if serv_norm not in opcoes_serv:
                            opcoes_serv.append(serv_norm)
                        idx_s = opcoes_serv.index(serv_norm)
                        
                        servico_confirm = st.selectbox("Confirmar Serviço", opcoes_serv, index=idx_s)
                    
                    vagas_cad = db.query(DisponibilidadeVaga).filter(
                        DisponibilidadeVaga.cidade == cidade_confirm,
                        DisponibilidadeVaga.tipo_servico == servico_confirm,
                        DisponibilidadeVaga.data >= date.today()
                    ).all()
                    
                    vagas_disp = []
                    for v in vagas_cad:
                        ag_qtd = db.query(Agendamento).filter_by(
                            data_agendamento=v.data, cidade=cidade_confirm, tipo_servico=servico_confirm, periodo=v.periodo
                        ).count()
                        if (v.vagas_totais - ag_qtd) > 0:
                            vagas_disp.append(v)
                            
                    if not vagas_disp:
                        st.error(f"⚠️ Não existem vagas cadastradas ou disponíveis para a cidade '{cidade_confirm}' e serviço '{servico_confirm}' na Gestão de Vagas.")
                        btn_agendar = st.form_submit_button("Confirmar Agendamento", disabled=True)
                    else:
                        datas_opt = sorted(list(set([v.data for v in vagas_disp])))
                        data_sel = st.selectbox("Escolha a Data do Agendamento", datas_opt, format_func=lambda d: d.strftime("%d/%m/%Y"))
                        
                        periodos_opt = [v.periodo for v in vagas_disp if v.data == data_sel]
                        periodo_sel = st.selectbox("Escolha o Período", periodos_opt)
                        
                        obs_sel = st.text_input("Observações do Agendamento")
                        btn_agendar = st.form_submit_button("Confirmar e Agendar Protocolo", type="primary")
                        
                        if btn_agendar:
                            novo_a = Agendamento(
                                cliente_id=p_sel.protocolo,
                                id_cliente=p_sel.id_cliente,
                                id_contrato=p_sel.id_contrato,
                                cidade=cidade_confirm,
                                tipo_servico=servico_confirm,
                                data_agendamento=data_sel,
                                periodo=periodo_sel,
                                observacoes=obs_sel,
                                status="Agendado",
                                agendado_por=usr["nome"],
                                criador_excel=p_sel.criador_excel,
                                nome_cliente=p_sel.nome_cliente,
                                rua=p_sel.rua,
                                bairro=p_sel.bairro,
                                categoria_4=p_sel.categoria_4,
                                dados_completos=True
                            )
                            db.add(novo_a)
                            p_sel.status = "Agendado"
                            db.commit()
                            st.session_state["msg_sucesso_pendente"] = f"✅ Protocolo {p_sel.protocolo} ({p_sel.nome_cliente or 'Cliente'}) agendado com sucesso para {data_sel.strftime('%d/%m/%Y')} ({periodo_sel})!"
                            st.rerun()
        finally:
            db.close()

    # -------------------------------------------------------------------------
    # MÓDULO 4: PAINEL DE AGENDA (VISUALIZAÇÃO 3 DIAS + RELATÓRIO)
    # -------------------------------------------------------------------------
    elif menu_selecionado == "4. Painel de Agenda (3 Dias)":
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
                                    "Agendado Por": getattr(c, 'agendado_por', None) or "-",
                                    "Criador (AK)": getattr(c, 'criador_excel', None) or "-",
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
                            "Agendado Por (Sistema)": getattr(a, 'agendado_por', None) or "-",
                            "Criador (Coluna AK)": getattr(a, 'criador_excel', None) or "-",
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
    # MÓDULO 5: IMPORTAÇÃO E GERENCIAMENTO DE EXCEL (.XLSX / .XLS)
    # -------------------------------------------------------------------------
    elif menu_selecionado == "5. Importação de Excel (.xlsx / .xls)":
        st.title("📥 Importação de Planilha e Gerenciamento de Dados")
        
        tab_imp, tab_del = st.tabs(["📥 Importar Excel", "🗑️ Gerenciar / Excluir Registros"])
        
        with tab_imp:
            arquivo_excel = st.file_uploader("1. Selecione o arquivo Excel (.xlsx ou .xls)", type=["xlsx", "xls"])
            data_referencia = st.date_input("2. Data de Referência dos Agendamentos", value=date.today(), format="DD/MM/YYYY")
            
            btn_processar = st.button("🚀 Processar e Atualizar Agendamentos", type="primary")
            
            if btn_processar:
                if not arquivo_excel:
                    st.warning("⚠️ Por favor, selecione e faça o upload de um arquivo Excel acima primeiro.")
                else:
                    df = pd.read_excel(arquivo_excel, dtype=str)
                    st.write("Visualização da Planilha Enviada:", df.head())
                    
                    db = get_db()
                    atualizados = 0
                    ignorados_recolhimento = 0
                    novos_pendentes = 0
                    
                    try:
                        todos_agendamentos = db.query(Agendamento).all()
                        
                        for _, row in df.iterrows():
                            tipo_geral = str(row.get('Tipo Geral', row.get('Tipo geral', ''))).strip()
                            if tipo_geral.lower() == 'recolhimento':
                                ignorados_recolhimento += 1
                                continue
                            
                            proto_excel = limpar_str(row.get('Protocolo'))
                            id_cli_excel = limpar_str(row.get('ID Cliente'))
                            id_con_excel = limpar_str(row.get('ID Contrato'))
                            
                            ids_linha = [i for i in [proto_excel, id_cli_excel, id_con_excel] if i != ""]
                            
                            if not ids_linha:
                                continue
                                
                            ag = None
                            for a_item in todos_agendamentos:
                                ids_banco = [limpar_str(a_item.cliente_id), limpar_str(getattr(a_item, 'id_cliente', '')), limpar_str(getattr(a_item, 'id_contrato', ''))]
                                if any(i in ids_linha for i in ids_banco if i != ""):
                                    ag = a_item
                                    break
                            
                            nome_c = str(row.get('Cliente', '')).strip() if pd.notna(row.get('Cliente')) else None
                            rua_base = str(row.get('Rua', '')).strip() if pd.notna(row.get('Rua')) else ""
                            num_rua = str(row.get('Nº Rua', '')).strip() if pd.notna(row.get('Nº Rua')) else ""
                            rua_c = f"{rua_base}, {num_rua}".strip(", ") if rua_base else None
                            bairro_c = str(row.get('Bairro', '')).strip() if pd.notna(row.get('Bairro')) else None
                            cidade_c = str(row.get('Cidade', row.get('Região', ''))).strip() if pd.notna(row.get('Cidade', row.get('Região', None))) else None
                            
                            cat_val = str(row.get('Catálogo', '')).strip() if pd.notna(row.get('Catálogo')) else ""
                            tg_val = str(row.get('Tipo Geral', '')).strip() if pd.notna(row.get('Tipo Geral')) else ""
                            servico_c = normalizar_servico(cat_val or tg_val)
                            
                            cat_4 = str(row.get('Categoria 4', '')).strip() if pd.notna(row.get('Categoria 4')) else None
                            criador_ak = str(row.get('Criador', '')).strip() if pd.notna(row.get('Criador')) else None
                            
                            if ag:
                                if nome_c: ag.nome_cliente = nome_c
                                if rua_c: ag.rua = rua_c
                                if bairro_c: ag.bairro = bairro_c
                                if cat_4 and ag.tipo_servico == "Reparo": ag.categoria_4 = cat_4
                                ag.agendado_por = ag.agendado_por or usr["nome"]
                                if criador_ak: ag.criador_excel = criador_ak
                                ag.dados_completos = True
                                atualizados += 1
                            else:
                                main_id = proto_excel or id_cli_excel or id_con_excel
                                
                                existe_p = db.query(ProtocoloPendente).filter(
                                    (ProtocoloPendente.protocolo == main_id) |
                                    (ProtocoloPendente.id_cliente == id_cli_excel) |
                                    (ProtocoloPendente.id_contrato == id_con_excel)
                                ).first()
                                
                                if existe_p:
                                    existe_p.protocolo = main_id
                                    existe_p.id_cliente = id_cli_excel
                                    existe_p.id_contrato = id_con_excel
                                    if nome_c: existe_p.nome_cliente = nome_c
                                    if cidade_c: existe_p.cidade = cidade_c
                                    if servico_c: existe_p.tipo_servico = servico_c
                                    if rua_c: existe_p.rua = rua_c
                                    if bairro_c: existe_p.bairro = bairro_c
                                    if cat_4: existe_p.categoria_4 = cat_4
                                    if criador_ak: existe_p.criador_excel = criador_ak
                                    if existe_p.status != "Agendado":
                                        existe_p.status = "Pendente"
                                    novos_pendentes += 1
                                else:
                                    novo_p = ProtocoloPendente(
                                        protocolo=main_id,
                                        id_cliente=id_cli_excel,
                                        id_contrato=id_con_excel,
                                        nome_cliente=nome_c,
                                        cidade=cidade_c,
                                        tipo_servico=servico_c,
                                        rua=rua_c,
                                        bairro=bairro_c,
                                        categoria_4=cat_4,
                                        agendado_por=usr["nome"],
                                        criador_excel=criador_ak,
                                        data_referencia=data_referencia,
                                        status="Pendente"
                                    )
                                    db.add(novo_p)
                                    novos_pendentes += 1

                        db.commit()
                        
                        st.markdown("---")
                        col_res1, col_res2, col_res3 = st.columns(3)
                        col_res1.metric("🟢 Agendamentos Enriquecidos", f"{atualizados} O.S.")
                        col_res2.metric("🟡 Salvos em Pendências", f"{novos_pendentes} O.S.")
                        col_res3.metric("⚪ Ignorados (Recolhimento)", f"{ignorados_recolhimento} O.S.")
                        
                        if novos_pendentes > 0:
                            st.warning(f"⚠️ **{novos_pendentes} protocolo(s)** do Excel foram carregados na **📌 Central de Pendências de Agendamento**!")

                    finally:
                        db.close()

        with tab_del:
            st.subheader("Exclusão e Limpeza de Dados Importados")
            db = get_db()
            try:
                col_del1, col_del2 = st.columns(2)
                
                with col_del1:
                    st.markdown("#### 1. Limpar Lista de Protocolos Pendentes")
                    total_p = db.query(ProtocoloPendente).filter_by(status="Pendente").count()
                    st.write(f"Atualmente existem **{total_p}** protocolos pendentes de agendamento.")
                    
                    if st.button("🗑️ Apagar TODOS os Pendentes", type="primary"):
                        db.query(ProtocoloPendente).delete()
                        db.commit()
                        st.success("Lista de pendentes zerada com sucesso!")
                        st.rerun()
                        
                with col_del2:
                    st.markdown("#### 2. Apagar Agendamentos por Data")
                    data_del = st.date_input("Selecione a Data para Apagar", value=date.today(), format="DD/MM/YYYY")
                    total_ag_data = db.query(Agendamento).filter_by(data_agendamento=data_del).count()
                    st.write(f"Existem **{total_ag_data}** agendamentos para o dia {data_del.strftime('%d/%m/%Y')}.")
                    
                    if st.button(f"🗑️ Apagar Agendamentos do dia {data_del.strftime('%d/%m/%Y')}"):
                        if total_ag_data > 0:
                            db.query(Agendamento).filter_by(data_agendamento=data_del).delete()
                            db.commit()
                            st.success(f"Agendamentos do dia {data_del.strftime('%d/%m/%Y')} apagados!")
                            st.rerun()
                        else:
                            st.info("Nenhum registro encontrado para apagar nesta data.")
            finally:
                db.close()

    # -------------------------------------------------------------------------
    # MÓDULO 6: GESTÃO DE USUÁRIOS (CADASTRO, EDIÇÃO E PERMISSÕES)
    # -------------------------------------------------------------------------
    elif menu_selecionado == "6. Gestão de Usuários":
        st.title("👤 Gestão de Usuários e Permissões")
        
        tab_cad, tab_edit, tab_list = st.tabs(["➕ Cadastrar Usuário", "✏️ Editar Usuário", "📋 Usuários Cadastrados"])
        
        PERFIS_DISPONIVEIS = ["suporte", "comercial", "gestor_logistica", "admin"]
        
        with tab_cad:
            with st.form("form_novo_usuario"):
                st.subheader("Cadastrar Novo Colaborador")
                nome_u = st.text_input("Nome Completo")
                email_u = st.text_input("E-mail (Login)")
                senha_u = st.text_input("Senha Inicial", type="password")
                perfil_u = st.selectbox("Perfil de Acesso", PERFIS_DISPONIVEIS)
                
                if st.form_submit_button("Cadastrar Usuário", type="primary"):
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
                                st.rerun()
                        finally:
                            db.close()
                    else:
                        st.warning("Preencha todos os campos obrigatórios.")
                        
        with tab_edit:
            st.subheader("Editar Cadastro / Alterar Setor do Colaborador")
            db = get_db()
            try:
                usuarios_db = db.query(Usuario).order_by(Usuario.nome).all()
                if not usuarios_db:
                    st.info("Nenhum usuário cadastrado para edição.")
                else:
                    dict_usuarios = {f"{u.nome} ({u.email}) - Perfil Atual: {u.perfil.upper()}": u.id for u in usuarios_db}
                    usr_selecionado_label = st.selectbox("Selecione o Usuário que deseja editar:", list(dict_usuarios.keys()))
                    usr_id = dict_usuarios[usr_selecionado_label]
                    
                    user_to_edit = db.query(Usuario).filter_by(id=usr_id).first()
                    
                    if user_to_edit:
                        with st.form("form_editar_usuario"):
                            col_e1, col_e2 = st.columns(2)
                            with col_e1:
                                novo_nome = st.text_input("Nome Completo", value=user_to_edit.nome)
                                novo_email = st.text_input("E-mail (Login)", value=user_to_edit.email)
                            with col_e2:
                                idx_perfil = PERFIS_DISPONIVEIS.index(user_to_edit.perfil) if user_to_edit.perfil in PERFIS_DISPONIVEIS else 0
                                novo_perfil = st.selectbox("Perfil / Setor de Acesso", PERFIS_DISPONIVEIS, index=idx_perfil)
                                novo_status = st.selectbox("Status da Conta", ["Ativo", "Inativo"], index=0 if user_to_edit.ativo else 1)
                            
                            st.markdown("---")
                            st.caption("🔒 **Redefinição de Senha (Opcional):** Preencha abaixo somente se desejar alterar a senha deste usuário.")
                            nova_senha_admin = st.text_input("Nova Senha", type="password", placeholder="Deixe em branco para manter a senha atual")
                            
                            btn_salvar_edit = st.form_submit_button("Salvar Alterações", type="primary", use_container_width=True)
                            
                            if btn_salvar_edit:
                                if not novo_nome or not novo_email:
                                    st.error("Nome e E-mail não podem ficar em branco.")
                                else:
                                    email_check = db.query(Usuario).filter(Usuario.email == novo_email.strip().lower(), Usuario.id != user_to_edit.id).first()
                                    if email_check:
                                        st.error("Este e-mail já pertence a outro usuário cadastrado.")
                                    else:
                                        user_to_edit.nome = novo_nome.strip()
                                        user_to_edit.email = novo_email.strip().lower()
                                        user_to_edit.perfil = novo_perfil
                                        user_to_edit.ativo = True if novo_status == "Ativo" else False
                                        
                                        if nova_senha_admin:
                                            user_to_edit.senha_hash = hash_senha(nova_senha_admin)
                                            
                                        db.commit()
                                        st.success(f"Cadastro de {user_to_edit.nome} atualizado com sucesso!")
                                        st.rerun()
            finally:
                db.close()
                
        with tab_list:
            st.subheader("Relação Geral de Usuários do Sistema")
            db = get_db()
            try:
                todos_u = db.query(Usuario).all()
                if todos_u:
                    dados_u = []
                    for u in todos_u:
                        dados_u.append({
                            "ID": u.id,
                            "Nome": u.nome,
                            "E-mail": u.email,
                            "Perfil / Setor": u.perfil.upper(),
                            "Status": "🟢 Ativo" if u.ativo else "🔴 Inativo"
                        })
                    st.dataframe(pd.DataFrame(dados_u), use_container_width=True, hide_index=True)
            finally:
                db.close()

    # -------------------------------------------------------------------------
    # MÓDULO 7: ALTERAR MINHA SENHA (DISPONÍVEL PARA TODOS OS COLABORADORES)
    # -------------------------------------------------------------------------
    elif menu_selecionado == "🔑 Alterar Minha Senha":
        st.title("🔑 Alterar Minha Senha")
        st.caption(f"Atualize a senha de acesso da conta de **{usr['nome']}** ({usr['email']}).")
        
        col_s1, col_s2 = st.columns([1, 1])
        with col_s1:
            with st.form("form_alterar_senha_propria", clear_on_submit=True):
                senha_atual = st.text_input("Senha Atual", type="password", placeholder="Digite sua senha atual")
                nova_senha = st.text_input("Nova Senha", type="password", placeholder="Mínimo 6 caracteres")
                confirma_nova = st.text_input("Confirmar Nova Senha", type="password", placeholder="Repita a nova senha")
                
                btn_mudar = st.form_submit_button("Atualizar Minha Senha", type="primary", use_container_width=True)
                
                if btn_mudar:
                    senha_atual_clean = senha_atual.strip()
                    nova_senha_clean = nova_senha.strip()
                    confirma_nova_clean = confirma_nova.strip()

                    if not senha_atual_clean or not nova_senha_clean or not confirma_nova_clean:
                        st.error("Por favor, preencha todos os campos do formulário.")
                    elif nova_senha_clean != confirma_nova_clean:
                        st.error("A nova senha e a confirmação não coincidem!")
                    elif len(nova_senha_clean) < 6:
                        st.error("Por motivos de segurança, a nova senha deve ter no mínimo 6 caracteres.")
                    else:
                        db = get_db()
                        try:
                            user_db = db.query(Usuario).filter_by(id=usr["id"]).first()
                            if not user_db:
                                st.error("Usuário não localizado no banco de dados.")
                            else:
                                # Verifica a senha atual
                                hash_atual_informada = hash_senha(senha_atual_clean)
                                
                                # Garante compatibilidade tanto para hash direto quanto para validações
                                if user_db.senha_hash != hash_atual_informada:
                                    st.error("A 'Senha Atual' informada está incorreta.")
                                else:
                                    # Atualiza com a nova hash
                                    user_db.senha_hash = hash_senha(nova_senha_clean)
                                    db.commit()
                                    
                                    st.success("🎉 Senha alterada com sucesso! Utilize sua nova senha no próximo login.")
                        except Exception as e:
                            db.rollback()
                            st.error(f"Erro ao atualizar senha no banco de dados: {str(e)}")
                        finally:
                            db.close()
