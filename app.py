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
        .main { background-color: #f8fafc; }
        .stMetric { background-color: white; padding: 15px; border-radius: 10px; border: 1px solid #e2e8f0; }
        .critical { color: #e11d48; font-weight: bold; }
        .justified { color: #059669; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)

    if 'logado' not in st.session_state:
        st.session_state.logado = False

    if not st.session_state.logado:
        tela_login()
    else:
        aba_principal()

def tela_login():
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<br><br><h1 style='text-align: center;'>🛡️ SENTINEL</h1>", unsafe_allow_html=True)
        email = st.text_input("E-mail Institucional").lower().strip()
        if email:
            res = supabase.table("colaboradores").select("*").eq("email", email).execute()
            if res.data:
                user = res.data[0]
                if not user.get('senha'):
                    s1 = st.text_input("Definir Senha", type="password")
                    if st.button("Ativar"):
                        supabase.table("colaboradores").update({"senha": s1}).eq("email", email).execute()
                        st.rerun()
                else:
                    senha = st.text_input("Senha", type="password")
                    if st.button("Entrar"):
                        if senha == user['senha']:
                            st.session_state.logado = True
                            st.session_state.usuario = user['nome']
                            st.session_state.permissao = user['permissao']
                            st.rerun()

def aba_principal():
    st.sidebar.title("SENTINEL 🛡️")
    menu = ["📝 Lançamento (Campo)", "📊 Análise de Frequência (SIS)"]
    escolha = st.sidebar.radio("Navegação", menu)
    
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    if "Lançamento" in escolha:
        tela_coleta_operacional()
    else:
        tela_analise_percentual()

def tela_coleta_operacional():
    st.subheader("📝 REGISTRO DE CAMPO")
    c1, c2 = st.columns(2)
    res_turmas = supabase.table("educandos").select("turma").execute()
    turmas = sorted(list(set([r['turma'] for r in res_turmas.data])))
    
    turma_sel = c1.selectbox("Turma", [""] + turmas)
    data_evento = c2.date_input("Data", datetime.now())

    if turma_sel:
        res_alunos = supabase.table("educandos").select("nome").eq("turma", turma_sel).order("nome").execute()
        lista_nomes = [a['nome'] for a in res_alunos.data]
        selecionados = st.multiselect("Educandos com ocorrência (Quadro):", lista_nomes)
        
        if selecionados:
            dados_para_salvar = []
            for nome in selecionados:
                with st.expander(f"Ajustar: {nome}", expanded=True):
                    col_t, col_o = st.columns([1, 2])
                    # Adicionada a categoria explícita de Justificada
                    tipo = col_t.selectbox("Tipo", ["Falta", "Falta Justificada (Atestado)", "Atraso", "Saída Antecipada"], key=f"t_{nome}")
                    obs = col_o.text_input("Observação", key=f"o_{nome}")
                    dados_para_salvar.append({
                        "aluno_nome": nome,
                        "data_evento": str(data_evento),
                        "tipo": tipo,
                        "observacao": f"{obs} | Por: {st.session_state.usuario}"
                    })
            
            if st.button("🚀 SALVAR REGISTROS"):
                supabase.table("movimentacao").insert(dados_para_salvar).execute()
                st.success("Dados enviados ao SIS!")
                st.balloons()

def tela_analise_percentual():
    st.subheader("📊 ANÁLISE E PERCENTUAIS")
    
    # 1. Busca dados
    res = supabase.table("movimentacao").select("*").execute()
    if not res.data:
        st.info("Sem dados para análise.")
        return

    df = pd.DataFrame(res.data)
    aluno_busca = st.text_input("Filtrar por Educando", placeholder="Ex: Arthur")

    if aluno_busca:
        df = df[df['aluno_nome'].str.contains(aluno_busca, case=False)]

    # 2. Lógica de Percentual
    # Vamos considerar um período de 20 dias letivos como base para o cálculo inicial
    base_dias = st.number_input("Base de Dias Letivos (para cálculo de %)", value=22, min_value=1)
    
    # Separação de Faltas Reais vs Justificadas
    faltas_reais = len(df[df['tipo'] == 'Falta'])
    faltas_just = len(df[df['tipo'] == 'Falta Justificada (Atestado)'])
    atrasos = len(df[df['tipo'] == 'Atraso'])

    perc_falta = (faltas_reais / base_dias) * 100

    # Dashboard de Indicadores
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Faltas Não Just.", faltas_reais)
    c2.metric("Justificadas", faltas_just)
    c3.metric("Atrasos", atrasos)
    
    # Cor do indicador de percentual
    cor_perc = "normal" if perc_falta < 15 else "inverse"
    c4.metric("Índice de Faltas %", f"{perc_falta:.1f}%", delta="Risco" if perc_falta > 20 else None, delta_color=cor_perc)

    st.write("---")
    st.markdown("#### Detalhamento de Ocorrências")
    # Tabela com cores para facilitar a leitura do SIS
    st.dataframe(df[['data_evento', 'tipo', 'observacao']].sort_values(by='data_evento', ascending=False), use_container_width=True)

if __name__ == "__main__":
    main()
