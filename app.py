import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

# --- CONEXÃO ---
URL = "https://dwbnfdgwtfubmemkakhg.supabase.co".strip()
KEY = "sb_publishable_7INEN7NrbcF72S2PVL0ENw_OEXlX3fH".strip()
supabase: Client = create_client(URL, KEY)

def main():
    st.set_page_config(page_title="SENTINEL - Gestão de Convivência", page_icon="🛡️", layout="wide")

    # CSS para Identidade Sentinel (Tecnológica e Profissional)
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
        
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        
        .main { background-color: #f8fafc; }
        
        /* Barra Lateral Sentinel */
        [data-testid="stSidebar"] {
            background-color: #0f172a;
            color: #f1f5f9;
        }
        [data-testid="stSidebar"] * { color: #f1f5f9 !important; }

        /* Estilo dos Cards de Histórico */
        .card { 
            background-color: white; 
            padding: 1.5rem; 
            border-radius: 12px; 
            border-left: 5px solid #1e293b;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
        }
        
        /* Título do Sistema */
        .sentinel-header {
            color: #0f172a;
            font-weight: 800;
            letter-spacing: -1px;
            margin-bottom: 0px;
        }
        
        /* Badge de Status */
        .badge {
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            background-color: #fee2e2;
            color: #b91c1c;
        }
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
        st.markdown("<br><br>", unsafe_allow_html=True)
        # Substitua o link abaixo pela sua logo se tiver
        st.markdown("<h1 style='text-align: center; color: #0f172a; font-size: 3rem;'>🛡️ SENTINEL</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #64748b;'>SISTEMA AUTÔNOMO DE SUPORTE À CONVIVÊNCIA</p>", unsafe_allow_html=True)
        
        with st.container():
            email = st.text_input("Identificação (E-mail)").lower().strip()
            
            if email:
                res = supabase.table("colaboradores").select("*").eq("email", email).execute()
                if res.data:
                    user = res.data[0]
                    if not user.get('senha'):
                        st.info("🔒 **Ativação de Credenciais**: Defina sua senha de acesso.")
                        s1 = st.text_input("Nova Senha", type="password")
                        s2 = st.text_input("Confirme a Senha", type="password")
                        if st.button("Ativar Acesso"):
                            if s1 == s2 and len(s1) >= 6:
                                supabase.table("colaboradores").update({"senha": s1}).eq("email", email).execute()
                                st.success("Acesso ativado com sucesso!")
                                st.rerun()
                    else:
                        senha = st.text_input("Senha", type="password")
                        if st.button("Acessar Painel Sentinel"):
                            if senha == user['senha']:
                                st.session_state.logado = True
                                st.session_state.usuario = user['nome']
                                st.session_state.cargo = user['funcao']
                                st.session_state.permissao = user['permissao']
                                st.rerun()
                            else:
                                st.error("Credenciais inválidas.")
                else:
                    st.error("Usuário não autorizado no Sentinel.")

def aba_principal():
    st.sidebar.markdown(f"### 👤 {st.session_state.usuario}")
    st.sidebar.markdown(f"**Função:** {st.session_state.cargo}")
    st.sidebar.divider()
    
    nivel = st.session_state.permissao
    menu = ["📊 Dashboard de Histórico"]
    if nivel in ['NIVEL 1', 'NIVEL 2']:
        menu.insert(0, "📡 Lançar Registros")
    
    escolha = st.sidebar.radio("Navegação Estratégica", menu)
    
    st.sidebar.divider()
    if st.sidebar.button("🔌 Desconectar"):
        st.session_state.logado = False
        st.rerun()

    # Título Dinâmico
    st.markdown(f"<h2 class='sentinel-header'>{escolha.upper()}</h2>", unsafe_allow_html=True)
    st.caption("Sentinel Intelligence Suite | Gerando suporte para o seu trabalho diário.")

    if "Lançar Registros" in escolha:
        tela_lancamento()
    else:
        tela_historico(nivel)

def tela_lancamento():
    st.write("---")
    res_turmas = supabase.table("educandos").select("turma").execute()
    if res_turmas.data:
        turmas = sorted(list(set([r['turma'] for r in res_turmas.data])))
        
        c1, c2 = st.columns([1, 1])
        turma_sel = c1.selectbox("Unidade / Turma", turmas)
        data_sel = c2.date_input("Data do Registro", datetime.now())

        if turma_sel:
            st.info("💡 **Dica Sentinel**: Registre atrasos e faltas para gerar histórico de suporte em reuniões de pais.")
            res_alunos = supabase.table("educandos").select("nome").eq("turma", turma_sel).order("nome").execute()
            alunos = [a['nome'] for a in res_alunos.data]
            
            registros = []
            for aluno in alunos:
                with st.container():
                    col_n, col_s, col_o = st.columns([1.5, 0.8, 2])
                    col_n.markdown(f"<p style='margin-top: 10px;'>{aluno}</p>", unsafe_allow_html=True)
                    status = col_s.selectbox("Status", ["Presente", "Falta", "Atraso", "Atestado"], key=f"s_{aluno}", label_visibility="collapsed")
                    
                    if status != "Presente":
                        obs = col_o.text_input("Observação Técnica", key=f"o_{aluno}", placeholder="Descreva brevemente o ocorrido...")
                        registros.append({
                            "aluno_nome": aluno,
                            "data_evento": str(data_sel),
                            "tipo": status,
                            "observacao": f"{obs} | Registrado por: {st.session_state.usuario}"
                        })
            
            if st.button("📥 FINALIZAR E ALIMENTAR BANCO DE DADOS"):
                if registros:
                    supabase.table("movimentacao").insert(registros).execute()
                    st.success("Dados integrados com sucesso ao sistema Sentinel!")
                else:
                    st.warning("Nenhum desvio registrado. Todos marcados como presente.")

def tela_historico(nivel):
    st.write("---")
    busca = st.text_input("🔍 Buscar Educando para Auditoria", placeholder="Digite o nome completo...")
    
    query = supabase.table("movimentacao").select("*").order("data_evento", desc=True)
    if busca:
        query = query.ilike("aluno_nome", f"%{busca}%")
    
    dados = query.limit(20).execute().data

    if dados:
        for row in dados:
            st.markdown(f"""
                <div class="card">
                    <span class="badge">{row['tipo']}</span>
                    <span style='margin-left: 10px; color: #64748b; font-size: 13px;'>📅 {row['data_evento']}</span>
                    <p style='margin: 10px 0 5px 0; font-weight: bold; color: #1e293b; font-size: 18px;'>{row['aluno_nome']}</p>
                    <p style='color: #475569; font-size: 14px;'>📄 <b>Anotação:</b> {row['observacao']}</p>
                </div>
            """, unsafe_allow_html=True)
            
            if nivel == 'NIVEL 1':
                if st.button(f"Remover Registro #{row['id'][:8]}", key=f"d_{row['id']}"):
                    supabase.table("movimentacao").delete().eq("id", row['id']).execute()
                    st.rerun()
    else:
        st.info("Nenhum dado encontrado para os critérios de busca.")

if __name__ == "__main__":
    main()
