import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

# --- CONEXÃO ---
URL = "https://dwbnfdgwtfubmemkakhg.supabase.co".strip()
KEY = "sb_publishable_7INEN7NrbcF72S2PVL0ENw_OEXlX3fH".strip()
supabase: Client = create_client(URL, KEY)

def main():
    st.set_page_config(page_title="SENTINEL - Intelligence", page_icon="🛡️", layout="wide")

    st.markdown("""
        <style>
        .main { background-color: #f1f5f9; }
        .stMetric { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        .dashboard-title { color: #0f172a; font-weight: 800; font-size: 24px; margin-bottom: 20px; border-bottom: 2px solid #e2e8f0; }
        </style>
    """, unsafe_allow_html=True)

    if 'logado' not in st.session_state:
        st.session_state.logado = False

    if not st.session_state.logado:
        tela_login()
    else:
        aba_principal()

# --- MANTENHA A tela_login E tela_coleta COMO ESTÃO (SÓ COPIE E COLE) ---
# [Aqui omiti por brevidade, mas você deve manter o código anterior delas]

def aba_principal():
    st.sidebar.title("SENTINEL")
    st.sidebar.markdown(f"👤 {st.session_state.usuario}")
    menu = ["📡 Coleta de Campo (Quadro)", "📊 Dashboard & Auditoria"]
    escolha = st.sidebar.radio("Módulos", menu)
    
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    if "Coleta de Campo" in escolha:
        tela_coleta() # Função que já fizemos
    else:
        tela_dashboard_avancado()

def tela_dashboard_avancado():
    st.markdown("<h2 class='dashboard-title'>📊 PAINEL DE INTELIGÊNCIA SIS</h2>", unsafe_allow_html=True)
    
    # Busca TODOS os dados para o Dashboard
    res = supabase.table("movimentacao").select("*").order("data_evento", desc=True).execute()
    if not res.data:
        st.info("Aguardando alimentação de dados...")
        return

    df = pd.DataFrame(res.data)
    df['data_evento'] = pd.to_datetime(df['data_evento']).dt.date

    # Filtros no Topo
    c1, c2, c3 = st.columns([2, 1, 1])
    aluno_filter = c1.text_input("🔍 Localizar Educando", placeholder="Ex: Arthur Tonial")
    data_inicio = c2.date_input("Início", datetime.now().replace(day=1))
    data_fim = c3.date_input("Fim", datetime.now())

    # Aplicar Filtros
    df_filtered = df[(df['data_evento'] >= data_inicio) & (df['data_evento'] <= data_fim)]
    if aluno_filter:
        df_filtered = df_filtered[df_filtered['aluno_nome'].str.contains(aluno_filter, case=False)]

    # --- MÉTRICAS DE IMPACTO ---
    st.write("### Resumo do Período")
    m1, m2, m3, m4 = st.columns(4)
    
    total_faltas = len(df_filtered[df_filtered['tipo'] == 'Falta'])
    total_atrasos = len(df_filtered[df_filtered['tipo'] == 'Atraso'])
    total_saidas = len(df_filtered[df_filtered['tipo'] == 'Saída Antecipada'])
    total_justificadas = len(df_filtered[df_filtered['tipo'] == 'Atestado'])

    m1.metric("Faltas", total_faltas, delta="Alerta" if total_faltas > 3 else None, delta_color="inverse")
    m2.metric("Atrasos", total_atrasos)
    m3.metric("Saídas Ant.", total_saidas)
    m4.metric("Justificadas", total_justificadas, help="Afastamentos médicos ou viagens autorizadas")

    st.write("---")

    # --- SEÇÕES SEPARADAS ---
    col_f, col_a = st.columns(2)

    with col_f:
        st.markdown("#### 🚫 Detalhamento de Faltas")
        df_faltas = df_filtered[df_filtered['tipo'].isin(['Falta', 'Atestado'])]
        if not df_faltas.empty:
            # Tabela organizada
            st.dataframe(df_faltas[['data_evento', 'aluno_nome', 'tipo', 'observacao']], 
                         use_container_width=True, hide_index=True)
        else:
            st.caption("Sem registros de falta no período.")

    with col_a:
        st.markdown("#### ⏳ Atrasos e Saídas")
        df_atrasos = df_filtered[df_filtered['tipo'].isin(['Atraso', 'Saída Antecipada'])]
        if not df_atrasos.empty:
            st.dataframe(df_atrasos[['data_evento', 'aluno_nome', 'tipo', 'observacao']], 
                         use_container_width=True, hide_index=True)
        else:
            st.caption("Sem registros de atrasos/saídas no período.")

    # --- ALERTA DE REINCIDÊNCIA ---
    if not df_filtered.empty:
        st.write("---")
        st.markdown("#### 🚨 Alerta de Reincidência (Top 5)")
        reincidentes = df_filtered['aluno_nome'].value_counts().head(5)
        for nome, qtd in reincidentes.items():
            if qtd >= 3:
                st.warning(f"**{nome}** possui {qtd} ocorrências registradas. Recomenda-se análise pedagógica.")

# Re-utilize as outras funções (tela_login, tela_coleta) que já estavam funcionando.
