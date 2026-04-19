import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

# --- CONEXÃO ---
URL = "https://dwbnfdgwtfubmemkakhg.supabase.co".strip()
KEY = "sb_publishable_7INEN7NrbcF72S2PVL0ENw_OEXlX3fH".strip()
supabase: Client = create_client(URL, KEY)

# --- CONFIGURAÇÃO DEFINITIVA ---
TABELA_ALUNOS = "educandos"
TABELA_MOV = "movimentacao"

def main():
    st.set_page_config(page_title="SENTINEL - Gestão Ativa", layout="wide", page_icon="🛡️")
    if 'logado' not in st.session_state: st.session_state.logado = False
    if not st.session_state.logado: tela_login()
    else: aba_principal()

def tela_login():
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<h1 style='text-align: center;'>🛡️ SENTINEL</h1>", unsafe_allow_html=True)
        email = st.text_input("E-mail Institucional").lower().strip()
        if email:
            try:
                res = supabase.table("colaboradores").select("*").eq("email", email).execute()
                if res.data:
                    user = res.data[0]
                    if not user.get('senha'):
                        s = st.text_input("Definir Senha de Acesso", type="password")
                        if st.button("Ativar Conta"):
                            supabase.table("colaboradores").update({"senha": s}).eq("email", email).execute()
                            st.rerun()
                    else:
                        senha = st.text_input("Senha", type="password")
                        if st.button("Entrar"):
                            if senha == user['senha']:
                                st.session_state.logado, st.session_state.usuario = True, user['nome']
                                st.rerun()
                            else: st.error("Senha incorreta.")
                else: st.error("Usuário não autorizado no sistema.")
            except Exception as e: st.error(f"Erro de conexão: {e}")

def aba_principal():
    st.sidebar.title("SENTINEL 🛡️")
    st.sidebar.markdown(f"👤 **{st.session_state.usuario}**")
    
    # Validação de integridade da base de 552 alunos
    try:
        total = supabase.table(TABELA_ALUNOS).select("id", count="exact").execute().count
        st.sidebar.metric("Alunos Cadastrados", total)
    except: st.sidebar.error("Erro ao acessar base de educandos.")

    menu = ["📝 Lançamento de Campo", "📊 Dashboard SIS (Consulta)"]
    escolha = st.sidebar.radio("Navegação", menu)
    
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    if "Lançamento" in escolha: tela_coleta()
    else: tela_consulta()

def tela_coleta():
    st.subheader("📝 REGISTRO DE CAMPO")
    try:
        # Puxa turmas da nova base unificada
        res_t = supabase.table(TABELA_ALUNOS).select("turma").execute()
        turmas = sorted(list(set([r['turma'] for r in res_t.data if r.get('turma')])))
        
        c1, c2 = st.columns(2)
        turma_sel = c1.selectbox("Selecione a Turma", [""] + turmas)
        data_ev = c2.date_input("Data da Ocorrência", datetime.now())

        if turma_sel:
            # Busca nomes e matrículas para garantir identificação única
            res_a = supabase.table(TABELA_ALUNOS).select("nome, matricula").eq("turma", turma_sel).order("nome").execute()
            dict_alunos = {f"{a['nome']} ({a['matricula']})": a['nome'] for a in res_a.data}
            selecionados = st.multiselect(f"Educandos da Turma {turma_sel}:", list(dict_alunos.keys()))
            
            if selecionados:
                dados_para_salvar = []
                for label in selecionados:
                    nome_aluno = dict_alunos[label]
                    with st.expander(f"Configurar Ocorrência: {label}", expanded=True):
                        col_t, col_o = st.columns([1, 2])
                        tipo = col_t.selectbox("Tipo", ["--- Selecione ---", "Falta", "Falta Justificada", "Atraso", "Saída Antecipada"], key=f"t_{label}")
                        obs = col_o.text_input("Observação (Opcional)", key=f"o_{label}")
                        
                        if tipo != "--- Selecione ---":
                            dados_para_salvar.append({
                                "aluno_nome": nome_aluno,
                                "turma": turma_sel,
                                "data_evento": str(data_ev),
                                "tipo": tipo,
                                "observacao": f"{obs} | Registrado por: {st.session_state.usuario}"
                            })
                
                if st.button("💾 SALVAR REGISTROS NO SIS"):
                    if len(dados_para_salvar) == len(selecionados):
                        supabase.table(TABELA_MOV).insert(dados_para_salvar).execute()
                        st.success(f"{len(dados_para_salvar)} registros sincronizados com sucesso!")
                        st.balloons()
                    else:
                        st.warning("⚠️ Atenção: Defina o 'Tipo' para todos os alunos selecionados.")
    except Exception as e:
        st.error(f"Erro na operação de campo: {e}")

def tela_consulta():
    st.subheader("📊 PAINEL DE CONSULTA E AUDITORIA SIS")
    try:
        res = supabase.table(TABELA_MOV).select("*").order("data_evento", desc=True).execute()
        if not res.data:
            st.info("Nenhum registro de movimentação encontrado até o momento.")
            return

        df = pd.DataFrame(res.data)
        
        c1, c2, c3 = st.columns([2, 1, 1])
        f_nome = c1.text_input("🔍 Localizar por nome do Educando")
        
        turmas_existentes = sorted(df['turma'].unique().tolist()) if 'turma' in df.columns else []
        f_turma = c2.selectbox("Filtrar por Turma", ["Todas"] + turmas_existentes)
        
        base_dias = c3.number_input("Dias Letivos no Mês", value=22, min_value=1)

        # Filtros dinâmicos
        if f_nome:
            df = df[df['aluno_nome'].str.contains(f_nome, case=False)]
        if f_turma != "Todas":
            df = df[df['turma'] == f_turma]

        # Métricas de Inteligência
        faltas_reais = len(df[df['tipo'] == 'Falta'])
        perc = (faltas_reais / base_dias) * 100 if base_dias > 0 else 0
        
        st.metric("Índice de Absenteísmo (Faltas Reais)", f"{faltas_reais} ocorrências", f"{perc:.1f}% de impacto mensal")

        st.write("---")
        # Exibição organizada com as colunas que o SIS precisa
        cols_view = ['data_evento', 'aluno_nome', 'turma', 'tipo', 'observacao']
        st.dataframe(df[[c for c in cols_view if c in df.columns]], use_container_width=True, hide_index=True)
        
    except Exception as e:
        st.error(f"Erro no processamento da consulta: {e}")

if __name__ == "__main__":
    main()
