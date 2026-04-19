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
        .stButton>button { width: 100%; background-color: #0f172a; color: white; }
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
                                st.session_state.permissao = user['permissao']
                                st.rerun()
                            else:
                                st.error("Senha incorreta.")
                else:
                    st.error("Usuário não autorizado.")
            except Exception as e:
                st.error(f"Erro de conexão: {e}")

def aba_principal():
    st.sidebar.title("SENTINEL 🛡️")
    st.sidebar.markdown(f"👤 {st.session_state.usuario}")
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
    
    try:
        # Busca turmas
        res_turmas = supabase.table("educandos").select("turma").execute()
        if res_turmas.data:
            turmas = sorted(list(set([r['turma'] for r in res_turmas.data if r.get('turma')])))
        else:
            turmas = []
            st.warning("Nenhuma turma encontrada na tabela 'educandos'.")
    except:
        turmas = []
        st.error("Falha ao carregar turmas.")

    c1, c2 = st.columns(2)
    turma_sel = c1.selectbox("Selecione a Turma", [""] + turmas)
    data_evento = c2.date_input("Data da Ocorrência", datetime.now())

    if turma_sel:
        st.write("---")
        try:
            res_alunos = supabase.table("educandos").select("nome").eq("turma", turma_sel).order("nome").execute()
            if res_alunos.data:
                lista_nomes = [a['nome'] for a in res_alunos.data]
                selecionados = st.multiselect(f"Educandos da Turma {turma_sel} (Quadro):", lista_nomes)
                
                if selecionados:
                    dados_para_salvar = []
                    for nome in selecionados:
                        with st.expander(f"Ajustar: {nome}", expanded=True):
                            col_t, col_o = st.columns([1, 2])
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
                        st.success("Dados sincronizados com sucesso!")
                        st.balloons()
            else:
                st.info("Nenhum aluno encontrado nesta turma.")
        except Exception as e:
            st.error(f"Erro ao buscar alunos: {e}")

def tela_analise_percentual():
    st.subheader("📊 ANÁLISE E PERCENTUAIS")
    
    try:
        res = supabase.table("movimentacao").select("*").execute()
        if not res.data:
            st.info("Ainda não há registros de movimentação para análise.")
            return

        df = pd.DataFrame(res.data)
        aluno_busca = st.text_input("🔍 Localizar por nome do educando...")

        if aluno_busca:
            df = df[df['aluno_nome'].str.contains(aluno_busca, case=False)]

        base_dias = st.number_input("Base de Dias Letivos (Mês)", value=22, min_value=1)
        
        # Filtros de inteligência
        f_reais = len(df[df['tipo'] == 'Falta'])
        f_just = len(df[df['tipo'] == 'Falta Justificada (Atestado)'])
        atrasos = len(df[df['tipo'] == 'Atraso'])
        perc = (f_reais / base_dias) * 100

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Faltas", f_reais)
        c2.metric("Justificadas", f_just)
        c3.metric("Atrasos", atrasos)
        c4.metric("% Faltas Reais", f"{perc:.1f}%")

        st.write("---")
        st.dataframe(df[['data_evento', 'aluno_nome', 'tipo', 'observacao']].sort_values(by='data_evento', ascending=False), use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"Erro ao processar dados: {e}")

if __name__ == "__main__":
    main()
