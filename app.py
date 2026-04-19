import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

# --- CONEXÃO ---
URL = "https://dwbnfdgwtfubmemkakhg.supabase.co".strip()
KEY = "sb_publishable_7INEN7NrbcF72S2PVL0ENw_OEXlX3fH".strip()
supabase: Client = create_client(URL, KEY)

# --- CONFIGURAÇÃO ---
TABELA_ALUNOS = "alunos_cadastro_2026"
TABELA_MOV = "movimentacao"

def main():
    st.set_page_config(page_title="SENTINEL - Intelligence", page_icon="🛡️", layout="wide")

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
            try:
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
                                st.rerun()
                            else: st.error("Senha incorreta.")
                else: st.error("Usuário não cadastrado.")
            except Exception as e: st.error(f"Erro: {e}")

def aba_principal():
    st.sidebar.title("SENTINEL 🛡️")
    st.sidebar.markdown(f"👤 {st.session_state.usuario}")
    
    # Contador de Alunos na base
    try:
        total_alunos = supabase.table(TABELA_ALUNOS).select("id", count="exact").execute().count
        st.sidebar.metric("Alunos Cadastrados", total_alunos)
    except: pass

    menu = ["📝 Lançamento de Campo", "📊 Dashboard SIS (Consulta)"]
    escolha = st.sidebar.radio("Navegação", menu)
    
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    if "Lançamento" in escolha:
        tela_coleta()
    else:
        tela_consulta_detalhada()

def tela_coleta():
    st.subheader("📝 REGISTRO DE CAMPO")
    try:
        res_turmas = supabase.table(TABELA_ALUNOS).select("turma").execute()
        turmas = sorted(list(set([r['turma'] for r in res_turmas.data if r.get('turma')])))
    except: turmas = []

    c1, c2 = st.columns(2)
    turma_sel = c1.selectbox("Selecione a Turma", [""] + turmas)
    data_evento = c2.date_input("Data", datetime.now())

    if turma_sel:
        res_alunos = supabase.table(TABELA_ALUNOS).select("nome").eq("turma", turma_sel).order("nome").execute()
        lista_nomes = [a['nome'] for a in res_alunos.data]
        selecionados = st.multiselect(f"Educandos da {turma_sel}:", lista_nomes)
        
        if selecionados:
            dados_salvar = []
            for nome in selecionados:
                with st.expander(f"Ajustar: {nome}", expanded=True):
                    col_t, col_o = st.columns([1, 2])
                    # Forçando a escolha do tipo para evitar erros
                    tipo = col_t.selectbox("Tipo de Ocorrência", 
                                         ["--- Selecione ---", "Falta", "Falta Justificada (Atestado)", "Atraso", "Saída Antecipada"], 
                                         key=f"t_{nome}")
                    obs = col_o.text_input("Observação/Motivo", key=f"o_{nome}")
                    
                    if tipo != "--- Selecione ---":
                        dados_salvar.append({
                            "aluno_nome": nome,
                            "turma": turma_sel, # Gravando a turma junto para facilitar consulta
                            "data_evento": str(data_evento),
                            "tipo": tipo,
                            "observacao": f"{obs} | Por: {st.session_state.usuario}"
                        })
            
            if st.button("🚀 FINALIZAR LANÇAMENTO"):
                if len(dados_salvar) < len(selecionados):
                    st.warning("⚠️ Selecione o tipo de ocorrência para todos os alunos antes de salvar.")
                else:
                    supabase.table(TABELA_MOV).insert(dados_salvar).execute()
                    st.success("Registros salvos com sucesso!")
                    st.balloons()

def tela_consulta_detalhada():
    st.subheader("📊 CONSULTA E AUDITORIA SIS")
    
    # Busca registros
    res = supabase.table(TABELA_MOV).select("*").order("data_evento", desc=True).execute()
    if not res.data:
        st.info("Aguardando registros.")
        return

    df = pd.DataFrame(res.data)

    # Filtros de Dashboard
    c1, c2, c3 = st.columns([2, 1, 1])
    f_nome = c1.text_input("🔍 Buscar Educando")
    
    # Filtro de Turma (Dinâmico)
    turmas_existentes = sorted(df['turma'].unique().tolist()) if 'turma' in df.columns else []
    f_turma = c2.selectbox("Filtrar por Turma", ["Todas"] + turmas_existentes)
    
    base_dias = c3.number_input("Dias Letivos", value=22)

    # Aplicação dos filtros no DataFrame
    if f_nome:
        df = df[df['aluno_nome'].str.contains(f_nome, case=False)]
    if f_turma != "Todas":
        df = df[df['turma'] == f_turma]

    # Métricas
    total_f = len(df[df['tipo'] == 'Falta'])
    total_j = len(df[df['tipo'] == 'Falta Justificada (Atestado)'])
    st.metric("Índice de Faltas Reais", f"{total_f} registros", delta=f"{((total_f/base_dias)*100):.1f}% de impacto")

    st.write("---")
    # Tabela com as colunas que você precisava
    colunas_exibir = ['data_evento', 'aluno_nome', 'turma', 'tipo', 'observacao']
    # Verifica se as colunas existem (segurança)
    cols_existentes = [c for c in colunas_exibir if c in df.columns]
    
    st.dataframe(df[cols_existentes], use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()
