import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

# --- CONEXÃO ---
URL = "https://dwbnfdgwtfubmemkakhg.supabase.co".strip()
KEY = "sb_publishable_7INEN7NrbcF72S2PVL0ENw_OEXlX3fH".strip()
supabase: Client = create_client(URL, KEY)

def main():
    st.set_page_config(page_title="SENTINEL - Registro de Campo", page_icon="🛡️", layout="wide")

    # CSS para foco em produtividade
    st.markdown("""
        <style>
        .main { background-color: #f8fafc; }
        .stButton>button { background-color: #0f172a; color: white; font-weight: bold; }
        .stMultiSelect [data-baseweb="tag"] { background-color: #0f172a !important; color: white !important; }
        .section-header { color: #0f172a; font-weight: 800; border-bottom: 2px solid #e2e8f0; padding-bottom: 5px; margin-bottom: 15px; }
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
        st.markdown("<p style='text-align: center;'>AUTENTICAÇÃO DE OPERADOR</p>", unsafe_allow_html=True)
        email = st.text_input("E-mail Institucional").lower().strip()
        if email:
            res = supabase.table("colaboradores").select("*").eq("email", email).execute()
            if res.data:
                user = res.data[0]
                if not user.get('senha'):
                    s1 = st.text_input("Definir Senha de Acesso", type="password")
                    if st.button("Ativar Acesso"):
                        supabase.table("colaboradores").update({"senha": s1}).eq("email", email).execute()
                        st.success("Acesso ativado!")
                        st.rerun()
                else:
                    senha = st.text_input("Senha", type="password")
                    if st.button("Entrar no Sistema"):
                        if senha == user['senha']:
                            st.session_state.logado = True
                            st.session_state.usuario = user['nome']
                            st.session_state.permissao = user['permissao']
                            st.rerun()
            else: st.error("Usuário não cadastrado.")

def aba_principal():
    st.sidebar.title("SENTINEL 🛡️")
    st.sidebar.info(f"Operador: {st.session_state.usuario}")
    
    menu = ["📝 Lançamento de Campo (Real-Time)", "📊 Consulta de Registros"]
    escolha = st.sidebar.radio("Navegação", menu)
    
    if st.sidebar.button("🔌 Sair"):
        st.session_state.logado = False
        st.rerun()

    if "Lançamento" in escolha:
        tela_coleta_operacional()
    else:
        tela_consulta_simples()

def tela_coleta_operacional():
    st.markdown("<h2 class='section-header'>📝 COLETA DE CAMPO (QUADRO)</h2>", unsafe_allow_html=True)
    
    # 1. Configuração da Coleta
    c1, c2 = st.columns(2)
    res_turmas = supabase.table("educandos").select("turma").execute()
    turmas = sorted(list(set([r['turma'] for r in res_turmas.data])))
    
    turma_sel = c1.selectbox("Selecione a Turma/Unidade", [""] + turmas)
    data_evento = c2.date_input("Data da Ocorrência", datetime.now(), help="Você pode selecionar datas passadas para lançar o retroativo.")

    if turma_sel:
        st.write("---")
        # 2. Busca Alunos
        res_alunos = supabase.table("educandos").select("nome").eq("turma", turma_sel).order("nome").execute()
        lista_nomes = [a['nome'] for a in res_alunos.data]
        
        st.markdown(f"### 👥 Alunos da Turma: {turma_sel}")
        st.caption("Selecione apenas quem NÃO está presente ou possui atraso.")
        
        selecionados = st.multiselect("Pesquisar e selecionar educandos:", lista_nomes)
        
        if selecionados:
            st.markdown("#### Detalhes das Ocorrências")
            dados_para_salvar = []
            
            for nome in selecionados:
                with st.expander(f"⚙️ Ajustar: {nome}", expanded=True):
                    col_t, col_o = st.columns([1, 2])
                    tipo = col_t.selectbox("Tipo", ["Falta", "Atraso", "Saída Antecipada", "Atestado"], key=f"tipo_{nome}")
                    obs = col_o.text_input("Observação / Motivo", key=f"obs_{nome}", placeholder="Ex: Viagem, Médico, Chegou 2ª aula...")
                    
                    dados_para_salvar.append({
                        "aluno_nome": nome,
                        "data_evento": str(data_evento),
                        "tipo": tipo,
                        "observacao": f"{obs} | Registrado por: {st.session_state.usuario}"
                    })
            
            st.write("---")
            if st.button("🚀 FINALIZAR LANÇAMENTO DA TURMA"):
                with st.spinner("Sincronizando com o banco de dados..."):
                    supabase.table("movimentacao").insert(dados_para_salvar).execute()
                    st.success(f"Sucesso! {len(dados_para_salvar)} registros salvos para a turma {turma_sel}.")
                    st.balloons()
                    # Pequeno delay para o usuário ver o sucesso antes de limpar
        else:
            st.info("Nenhum educando selecionado. Todos desta turma serão considerados PRESENTES.")

def tela_consulta_simples():
    st.markdown("<h2 class='section-header'>📊 CONSULTA RÁPIDA</h2>", unsafe_allow_html=True)
    busca = st.text_input("🔍 Buscar por nome do educando...")
    
    query = supabase.table("movimentacao").select("*").order("data_evento", desc=True)
    if busca:
        query = query.ilike("aluno_nome", f"%{busca}%")
    
    resultado = query.limit(20).execute().data
    if resultado:
        df = pd.DataFrame(resultado)
        st.dataframe(df[['data_evento', 'aluno_nome', 'tipo', 'observacao']], use_container_width=True, hide_index=True)
    else:
        st.write("Nenhum registro encontrado.")

if __name__ == "__main__":
    main()
