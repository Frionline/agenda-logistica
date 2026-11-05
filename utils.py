import streamlit as st
import pandas as pd

CIDADES = [
    "Nova Friburgo", "Lumiar", "Bom Jardim", "Duas Barras", 
    "Cordeiro e Cantagalo", "Macuco", "Trajano e Madalena", "São Fidelis",
    "Itaocara", "Cardoso Moreira", "Cambuci", "Italva"
]

SERVICOS = [
    "Reparo", "Instalação", "Mudança de Endereço", "Upgrade", "Alteração de Ponto"
]

def aplicar_estilo_css():
    st.markdown("""
    <style>
        :root {
            --primary-orange: #FF6600;
            --hover-orange: #E05500;
            --light-orange-bg: #FFF5EF;
            --dark-navy: #1E293B;
        }
        
        .stButton > button {
            border-radius: 8px !important;
            font-weight: 600 !important;
            transition: all 0.25s ease-in-out !important;
            border: 1.5px solid #CBD5E1 !important;
            background-color: #FFFFFF !important;
            color: #0F172A !important;
            height: 2.75rem !important;
        }
        
        .stButton > button:hover {
            border-color: #DC2626 !important;
            color: #DC2626 !important;
            background-color: #FEF2F2 !important;
            box-shadow: 0px 4px 14px rgba(220, 38, 38, 0.25) !important;
            transform: translateY(-2px) !important;
        }
        
        .stButton > button[kind="primary"], button[data-testid="stBaseButton-primary"] {
            background: linear-gradient(135deg, #FF6600 0%, #E05500 100%) !important;
            color: #FFFFFF !important;
            border: none !important;
            box-shadow: 0px 3px 8px rgba(255, 102, 0, 0.3) !important;
            height: 2.75rem !important;
        }
        
        .stButton > button[kind="primary"]:hover, button[data-testid="stBaseButton-primary"]:hover {
            background: linear-gradient(135deg, #FF7711 0%, #F06000 100%) !important;
            border: 1.5px solid #FF8822 !important;
            color: #FFFFFF !important;
            box-shadow: 0px 6px 16px rgba(255, 102, 0, 0.45) !important;
            transform: translateY(-2px) !important;
        }
        
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
        
        section[data-testid="stSidebar"] {
            background-color: #1E293B !important;
            border-right: 1px solid #334155 !important;
        }
        
        section[data-testid="stSidebar"] * {
            color: #F1F5F9 !important;
        }
    </style>
    """, unsafe_allow_html=True)

def limpar_str(val):
    if pd.isna(val) or val is None:
        return ""
    val_str = str(val).strip()
    if val_str.endswith(".0"):
        val_str = val_str[:-2]
    return val_str

def normalizar_cidade(cidade_str):
    if not cidade_str or pd.isna(cidade_str):
        return CIDADES[0]
    c = str(cidade_str).strip()
    c_lower = c.lower()
    if "cordeiro" in c_lower or "cantagalo" in c_lower:
        return "Cordeiro e Cantagalo"
    elif "trajano" in c_lower or "madalena" in c_lower:
        return "Trajano e Madalena"
    for cid in CIDADES:
        if cid.lower() in c_lower:
            return cid
    return c

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
