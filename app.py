import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime, timedelta

# --- CONEXÃO ---
URL = "https://dwbnfdgwtfubmemkakhg.supabase.co".strip()
KEY = "sb_publishable_7INEN7NrbcF72S2PVL0ENw_OEXlX3fH".strip()
supabase: Client = create_client(URL, KEY)

def main():
    st.set_page_config(page_title="SENTINEL - Intelligence", page_icon="🛡️", layout="wide")

    # CSS para uma interface limpa e focada em dados
    st.markdown("""
        <style>
        .main { background-color: #f8fafc; }
        .stMultiSelect [data-baseweb="tag"] { background-color: #0f172a !important; color: white !important; }
        .card-alerta { 
            background-color: #fff1f2; padding: 15px; border-radius: 10px; 
            border-left: 5px solid #e11d48; margin-bottom: 10px; 
        }
        .sentinel-header { color: #0f172a; font-weight: 800; margin-bottom: 0px; }
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
        st.markdown("<p style='text-align: center;'>SISTEMA AUTÔNOMO DE SUPORTE À CONVIVÊNCIA</p>", unsafe_allow_html=True)
        email = st.text_input("E-mail Institucional").lower().strip()
        if email:
            res = supabase.table("colaboradores").select("*").eq("email", email).execute()
            if res.data:
                user = res.data[0]
                if not user.get('senha'):
                    s1 = st.text_input("Criar Senha", type="password")
                    if st.button("Ativar Acesso"):
                        supabase.table("colaboradores").update({"senha": s1}).eq("email", email).execute()
                        st.success("Acesso ativado!")
                        st.rerun()
                else:
                    senha = st.text_input("Senha", type="password")
                    if st.button("Entrar"):
                        if senha == user['senha']:
                            st.session_state.logado = True
                            st.session_state.usuario = user['nome']
                            st.session_state.permissao = user['permissao']
                            st.rerun()
            else: st.error("Não autorizado.")

def aba_principal():
    st.sidebar.title("SENTINEL")
    st.sidebar.markdown(f"👤 {st.session_state.usuario}")
    
    menu = ["📡 Coleta de Campo (Quadro)", "📊 Inteligência & Relatórios"]
    escolha = st.sidebar.radio("Módulos", menu)
    
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    if "Coleta de Campo" in escolha:
        tela_coleta()
    else:
        tela_analise()

def tela_coleta():
    st.markdown("<h2 class='sentinel-header'>📡 REGISTRO DE CAMPO</h2>", unsafe_allow_html=True)
    st.caption("Coleta de informações de frequência para alimentação do SIS.")
    
    res_turmas = supabase.table("educandos").select("turma").execute()
    turmas = sorted(list(set([r['turma'] for r in res_turmas.data])))
    
    col1, col2 = st.columns(2)
    turma_sel = col1.selectbox("Selecione a Unidade/Turma", [""] + turmas)
    data_sel = col2.date_input("Data da Coleta (Ocorrência)", datetime.now())

    if turma_sel:
        st.write("---")
        # Busca alunos da turma
        res_alunos = supabase.table("educandos").select("nome").eq("turma", turma_sel).order("nome").execute()
        lista_nomes = [a['nome'] for a in res_alunos.data]
        
        st.markdown(f"### 📍 Educandos da Turma {turma_sel}")
        st.info("Todos são considerados **PRESENTES** por padrão. Selecione apenas os que possuem ocorrência no quadro.")
        
        ausentes = st.multiselect("Selecione os educandos com Falta/Atraso/Saída:", lista_nomes)
        
        if ausentes:
            st.warning(f"Registrando ocorrências para {len(ausentes)} educandos.")
            detalhes = []
            for nome in ausentes:
                with st.expander(f"Detalhes: {nome}", expanded=True):
                    c1, c2 = st.columns([1, 2])
                    tipo = c1.selectbox("Tipo", ["Falta", "Atraso", "Saída Antecipada", "Atestado"], key=f"t_{nome}")
                    obs = c2.text_input("Observação (Opcional)", key=f"o_{nome}")
                    detalhes.append({
                        "aluno_nome": nome,
                        "data_evento": str(data_sel),
                        "tipo": tipo,
                        "observacao": f"{obs} | Coletado por: {st.session_state.usuario}"
                    })
            
            if st.button("💾 SINCRONIZAR COM O SIS"):
                supabase.table("movimentacao").insert(detalhes).execute()
                st.success("Dados sincronizados! A inteligência do SIS já pode processar estes registros.")
                st.balloons()

def tela_analise():
    st.markdown("<h2 class='sentinel-header'>📊 INTELIGÊNCIA & AUDITORIA</h2>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Alertas Críticos", "Busca por Período"])
    
    with tab1:
        st.markdown("### ⚠️ Educandos com Frequência Crítica")
        # Lógica de Inteligência: Busca as últimas movimentações
        dados = supabase.table("movimentacao").select("*").order("data_evento", desc=True).limit(100).execute().data
        
        if dados:
            df = pd.DataFrame(dados)
            # Exemplo de análise: Contar faltas recentes por aluno
            faltas_count = df[df['tipo'] == 'Falta']['aluno_nome'].value_counts()
            criticos = faltas_count[faltas_count >= 3].index.tolist()
            
            if criticos:
                for aluno in criticos:
                    st.markdown(f"""
                        <div class='card-alerta'>
                            <strong>ALERTA SIS:</strong> {aluno} atingiu 3 ou mais faltas registradas recentemente.<br>
                            <small>Ação sugerida: Contato com responsáveis para verificação de abandono ou doença.</small>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.success("Nenhum padrão crítico detectado nas últimas coletas.")

    with tab2:
        st.write("Filtre dados para reuniões com responsáveis.")
        aluno_busca = st.text_input("Nome do Educando")
        if aluno_busca:
            historico = supabase.table("movimentacao").select("*").ilike("aluno_nome", f"%{aluno_busca}%").execute().data
            if historico:
                st.table(pd.DataFrame(historico)[['data_evento', 'tipo', 'observacao']])
            else:
                st.write("Nada consta no banco Sentinel.")

if __name__ == "__main__":
    main()
