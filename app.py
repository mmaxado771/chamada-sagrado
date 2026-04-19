def tela_coleta_operacional():
    st.subheader("📝 REGISTRO DE CAMPO")
    
    # Busca turmas com tratamento de erro
    try:
        res_turmas = supabase.table("educandos").select("turma").execute()
        if res_turmas.data:
            # Filtra turmas únicas e remove valores nulos
            turmas = sorted(list(set([r['turma'] for r in res_turmas.data if r.get('turma')])))
        else:
            turmas = []
            st.error("⚠️ Nenhuma turma encontrada na tabela 'educandos'. Verifique se os dados foram importados.")
    except Exception as e:
        st.error(f"Erro ao conectar com a tabela educandos: {e}")
        turmas = []

    c1, c2 = st.columns(2)
    turma_sel = c1.selectbox("Turma", [""] + turmas)
    data_evento = c2.date_input("Data", datetime.now())

    if turma_sel:
        # Busca alunos da turma selecionada
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
                        st.success("Dados enviados ao SIS!")
                        st.balloons()
            else:
                st.warning(f"Não encontramos alunos cadastrados na turma {turma_sel}.")
        except Exception as e:
            st.error(f"Erro ao buscar alunos: {e}")
