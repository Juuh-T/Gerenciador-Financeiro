import streamlit as st
import pandas as pd

st.set_page_config(page_title="Gerenciador Financeiro", layout="wide")
if "transacoes" not in st.session_state:
    st.session_state["transacoes"] = []

st.title("💰 Gerenciador Financeiro")
st.write("Controle suas receitas, despesas e metas financeiras em um só lugar")

st.sidebar.title("Navegação")
pagina = st.sidebar.radio("Selecione a página", ["Dashboard", "Transações", "Orçamentos", "Metas", "Relatórios", "Conversor de Moedas"])

# ------------------------------------------------------------------------------------------------------------------------------------ #

if pagina == "Dashboard":
    st.subheader("Visão Geral")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="Saldo Atual", value=None, border=True)
    with col2:
        st.metric(label="Receita do Mês", value=None, border=True)
    with col3:
        st.metric(label="Despesas do Mês", value=None, border=True)
    with col4:
        st.metric(label="Economia do Mês", value=None, border=True)


elif pagina == "Transações":
    st.subheader("Minhas Transações")

    with st.container(border=True):
        st.write("Nova Transação")
        tipo = st.selectbox("Tipo", ["Receita", "Despesa"])

        categorias_receita = ["Salário", "Freelance", "Investimentos", "Presente", "Outros"]
        categorias_despesa = ["Alimentação", "Transporte", "Saúde", "Educação", "Lazer", "Moradia", "Outros"]
        
        if tipo == "Receita":
            categorias_disponiveis = categorias_receita
        else:
            categorias_disponiveis = categorias_despesa

        with st.form("form_transacao", border=False):
            descricao = st.text_input("Descrição")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                valor = st.number_input("Valor (R$)", min_value=0.01, step=0.01, format="%.2f")
            with col2:
                categoria = st.selectbox("Categoria", categorias_disponiveis)
            with col3:
                data = st.date_input("Data")

            observacao_opcional = st.text_area("Observação (opcional)")
            botao = st.form_submit_button("Salvar Transação")


        if botao:
            if not descricao.strip():
                st.error("Digite uma descrição para a transação")
            else:
                nova_transacao = {
                    "descricao": descricao.strip(),
                    "valor": valor,
                    "tipo": tipo,
                    "categoria": categoria,
                    "data": data,
                    "observacao": observacao_opcional
                }
                st.session_state["transacoes"].append(nova_transacao)
                st.success("Transação cadastrada com sucesso!")

        if st.session_state["transacoes"]:
            df = pd.DataFrame(st.session_state["transacoes"])
            df["data"] = pd.to_datetime(df["data"]).dt.strftime("%d/%m/%Y")

            st.dataframe(df, hide_index=True, column_config={
                "descricao": "Descrição",
                "tipo": "Tipo",
                "categoria": "Categoria",
                "observacao": "Observação",
                "data": "Data",
                "valor": st.column_config.NumberColumn("Valor (R$)", alignment="left", format="R$ %.2f")
            })
        else:
            st.info("Nenhuma transação cadastrada.")


elif pagina == "Orçamentos":
    st.subheader("Controle de Orçamentos")


elif pagina == "Metas":
    st.subheader("Minhas Metas")


elif pagina == "Relatórios":
    st.subheader("Relatórios Financeiros")


elif pagina == "Conversor de Moedas":
    st.subheader("Conversor de Moedas")