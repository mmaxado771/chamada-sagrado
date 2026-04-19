import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

# --- CONEXÃO (Substitua pelos seus dados do Supabase) ---
URL = "SUA_URL_AQUI"
KEY = "SUA_ANON_KEY_AQUI"
supabase: Client = create_client(URL, KEY)

def main():
    st.set_page_config(page_title="Sistema Sagrado", page_icon="📝")

    if 'logado' not in st.session_state:
        st.session_state.logado = False

    if not st.session_state.logado:
        tela_login()
    else:
        nivel = st.session_state.permissao
        
        st.sidebar.title(f"👤 {st.session_state.usuario}")
        st.sidebar.write(f"🏷️ {st.session_state.cargo}")
        st.sidebar.info(f"🔑 Acesso: {nivel}")

        menu = ["Consultar Histórico"]
        # NIVEL 1 e NIVEL 2 podem lançar chamadas
        if nivel in ['NIVEL 1', 'NIVEL 2']:
            menu.insert(0, "Lançar Frequência")
        
        escolha = st.sidebar.radio("Navegação", menu)

        if st.sidebar.button("Sair"):
            st.session_state.logado = False
            st.rerun()

        if escolha == "Lançar Frequência":
            tela_lancamento()
        else:
            tela_historico(nivel)

def tela_login():
    st.title("🛡️ Sistema de Frequência")
    email = st.text_input("Digite seu E-mail Institucional").lower().strip()
    
    if email:
        res = supabase.table("colaboradores").select("*").eq("email", email).execute()
        if res.data:
            user = res.data[0]
            # Se a senha for NULL (como acabamos de resetar), força criação
            if not user.get('senha'):
                st.warning("Primeiro acesso! Crie sua senha:")
                s1 = st.text_input("Nova Senha", type="password")
                s2 = st.text_input("Confirme a Senha", type="password")
                if st.button("Ativar Conta"):
                    if s1 == s2 and len(s1) >= 6:
                        supabase.table("colaboradores").update({"senha": s1}).eq("email", email).execute()
                        st.success("Senha cadastrada! Entre agora com sua nova senha.")
                        st.rerun()
                    else:
                        st.error("Senhas não coincidem ou são curtas (mín. 6 caracteres).")
            else:
                senha = st.text_input("Senha", type="password")
                if st.button("Entrar"):
                    if senha == user['senha']:
                        st.session_state.logado = True
                        st.session_state.usuario = user['nome']
                        st.session_state.cargo = user['funcao']
                        st.session_state.permissao = user['permissao']
                        st.rerun()
                    else:
                        st.error("Senha incorreta.")
        else:
            if st.button("Entrar"):
                st.error("E-mail não cadastrado na base de dados.")

def tela_lancamento():
    st.header("📝 Registro de Chamada")
    res_turmas = supabase.table("educandos").select("turma").execute()
    if res_turmas.data:
        lista_turmas = sorted(list(set([r['turma'] for r in res_turmas.data])))
        turma_sel = st.selectbox("Selecione a Turma", lista_turmas)
        data_sel = st.date_input("Data da Ocorrência", datetime.now())

        if turma_sel:
            res_alunos = supabase.table("educandos").select("nome").eq("turma", turma_sel).order("nome").execute()
            alunos = [a['nome'] for a in res_alunos.data]
            
            registros = []
            for aluno in alunos:
                col1, col2 = st.columns([2, 1])
                col1.write(f"**{aluno}**")
                status = col2.selectbox("Status", ["Presente", "Falta", "Atraso", "Atestado"], key=f"l_{aluno}", label_visibility="collapsed")
                
                if status != "Presente":
                    obs = st.text_input(f"Observação ({aluno})", key=f"obs_{aluno}")
                    registros.append({
                        "aluno_nome": aluno,
                        "data_evento": str(data_sel),
                        "tipo": status,
                        "observacao": f"{obs} (Por: {st.session_state.usuario})".strip()
                    })
            
            if st.button("💾 SALVAR NO SISTEMA", type="primary"):
                if registros:
                    supabase.table("movimentacao").insert(registros).execute()
                    st.success("Registros salvos com sucesso!")
                    st.balloons()
                else:
                    st.info("Todos marcados como presente. Nada para salvar.")

def tela_historico(nivel):
    st.header("🔍 Consulta de Histórico")
    busca = st.text_input("Filtrar por nome do aluno")
    
    query = supabase.table("movimentacao").select("*").order("data_evento", desc=True)
    if busca:
        query = query.ilike("aluno_nome", f"%{busca}%")
    
    dados = query.limit(50).execute().data

    if dados:
        for row in dados:
            with st.expander(f"{row['data_evento']} - {row['aluno_nome']} ({row['tipo']})"):
                st.write(f"Anotação: {row['observacao']}")
                if nivel == 'NIVEL 1':
                    if st.button("🗑️ Excluir", key=f"del_{row['id']}"):
                        supabase.table("movimentacao").delete().eq("id", row['id']).execute()
                        st.rerun()
                else:
                    st.caption("🔒 Somente administradores podem excluir registros.")
    else:
        st.write("Nenhum registro encontrado.")

if __name__ == "__main__":
    main()