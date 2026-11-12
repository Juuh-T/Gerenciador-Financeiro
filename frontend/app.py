import streamlit as st
import pandas as pd
from datetime import date
from uuid import uuid4
from api import (
    buscar_transacoes, 
    buscar_resumo_dashboard, 
    criar_transacao,
    buscar_orcamentos,
    criar_orcamento,
    buscar_metas,
    criar_meta,
    atualizar_valor_meta,
    excluir_meta_api
)
st.set_page_config(page_title="Gerenciador Financeiro", layout="wide")

if "orcamentos" not in st.session_state:
    st.session_state["orcamentos"] = []
if "metas" not in st.session_state:
    st.session_state["metas"] = []

if "pagina_atual" not in st.session_state:
    st.session_state["pagina_atual"] = "Dashboard" 

st.title("💰 Gerenciador Financeiro")
st.write("Controle suas receitas, despesas e metas financeiras em um só lugar")

# ------------------------------------------------------------------------------------------------------------------------------------ #
# MENU LATERAL

st.sidebar.title("Finanças")
st.sidebar.caption("GERENCIADOR FINANCEIRO")
st.sidebar.divider()

def navegar(destino):
    st.session_state["pagina_atual"] = destino

paginas = {
    "Dashboard": ":material/dashboard:",
    "Transações": ":material/swap_horiz:",
    "Orçamentos": ":material/account_balance_wallet:",
    "Metas": ":material/flag:",
    "Relatórios": ":material/bar_chart:",
    "Conversor de Moedas": ":material/currency_exchange:"
}

for nome, icone in paginas.items():
    st.sidebar.button(
        nome, icon=icone, key=f"menu_{nome}", width="stretch",
        type="primary" if st.session_state["pagina_atual"] == nome else "secondary",
        on_click=navegar, args=(nome,)
    )
pagina = st.session_state["pagina_atual"]

# ------------------------------------------------------------------------------------------------------------------------------------ #
# DASHBOARD

if pagina == "Dashboard":
    st.subheader("Visão Geral")
    dados = buscar_resumo_dashboard()

    # Primeira linha
    col1, col2 = st.columns(2, gap="small")
    with col1:
        st.metric(label="Saldo Atual", value=f"R$ {dados['saldo_atual']:.2f}", border=True)
    with col2:
        st.metric(label="Receita do Mês", value=f"R$ {dados['receita_mes']:.2f}", border=True)

    # Segunda linha
    col3, col4 = st.columns(2, gap="small")
    with col3:
        st.metric(label="Despesas do Mês", value=f"R$ {dados['despesa_mes']:.2f}", border=True)
    with col4:
        st.metric(label="Economia do Mês", value=f"R$ {dados['economia_mes']:.2f}", border=True)

# ------------------------------------------------------------------------------------------------------------------------------------ #
# TRANSAÇÕES

elif pagina == "Transações":
    st.subheader("Minhas Transações")

    with st.container(border=True):
        st.write("Nova Transação")
        tipo = st.selectbox("Tipo", ["Receita", "Despesa"])

        categorias_receita = ["Salário", "Freelance", "Investimentos", "Presente", "Outros"]
        categorias_despesa = ["Alimentação", "Transporte", "Saúde", "Educação", "Lazer", "Moradia", "Outros"]
        
        categorias_disponiveis = categorias_receita if tipo == "Receita" else categorias_despesa

        with st.form("form_transacao", border=False):
            descricao = st.text_input("Descrição")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                valor = st.number_input("Valor (R$)", min_value=0.01, step=0.01, format="%.2f")
            with col2:
                categoria = st.selectbox("Categoria", categorias_disponiveis)
            with col3:
                data_transacao = st.date_input("Data")

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
                        "data": str(data_transacao),
                        "observacao": observacao_opcional
                    }
                    if criar_transacao(nova_transacao):
                        st.success("Transação salva")
                        st.rerun()
                    else:
                        st.error("Erro ao conectar com o servidor")

    st.write("---")
    transacao_salva = buscar_transacoes()
    
    if transacao_salva:
        df = pd.DataFrame(transacao_salva)
        
        col_filtro1, col_filtro2 = st.columns(2)
        with col_filtro1:
            filtro_tipo = st.selectbox("Filtrar por tipo", ["Todos", "Receita", "Despesa"])
        
        if filtro_tipo != "Todos":
            df = df[df["tipo"] == filtro_tipo]

        categorias_filtro = sorted(df["categoria"].dropna().unique())
        opcoes_categoria = ["Todas"] + list(categorias_filtro)

        with col_filtro2:
            filtro_categoria = st.selectbox("Filtrar por categoria", opcoes_categoria)
        
        if filtro_categoria != "Todas":
            df = df[df["categoria"] == filtro_categoria]

        if "_id" in df.columns:
            df = df.drop(columns=["_id"])
        if "data" in df.columns:
            df["data"] = pd.to_datetime(df["data"]).dt.strftime("%d/%m/%Y")

        st.dataframe(
            df,
            hide_index=True,
            column_config={
                "descricao": "Descrição",
                "tipo": "Tipo",
                "categoria": "Categoria",
                "data": "Data",
                "observacao": "Observação",
                "valor": st.column_config.NumberColumn("Valor (R$)", alignment="left", format="R$ %.2f")
            }
        )
    else:
        st.info("Nenhuma Transação Cadastrada")

# ------------------------------------------------------------------------------------------------------------------------------------ #
# ORÇAMENTOS (INTEGRADO À API FASTAPI / MONGODB)

elif pagina == "Orçamentos":
    st.subheader("Controle de Orçamentos")
    st.write("Defina seus limites mensais e acompanhe os gastos por categoria em tempo real.")

    with st.container(border=True):
        st.write("**Novo Orçamento**")

        with st.form("form_orcamento", border=False):
            categoria_orc = st.selectbox(
                "Categoria", 
                ["Alimentação", "Transporte", "Saúde", "Educação", "Lazer", "Moradia", "Outros"]
            )
            limite = st.number_input(
                "Limite mensal (R$)", min_value=0.01, step=0.01, format="%.2f"
            )

            botao_orcamento = st.form_submit_button("Salvar Orçamento")

            if botao_orcamento:
                novo_orcamento = {
                    "categoria": categoria_orc,
                    "limite": limite
                }
                if criar_orcamento(novo_orcamento):
                    st.success(f"Orçamento para {categoria_orc} salvo com sucesso!")
                    st.rerun()
                else:
                    st.error("Erro ao salvar orçamento no servidor.")

    st.write("---")
    st.subheader("Meus Orçamentos")
    orcamentos = buscar_orcamentos()

    if orcamentos:
        cards = st.columns(2)
        for posicao, item in enumerate(orcamentos):
            cat = item.get("categoria", "Sem Categoria")
            lim = float(item.get("limite", 0.0))
            gasto = float(item.get("gasto_atual", 0.0))
            pct = float(item.get("percentual", 0.0))

            with cards[posicao % 2]:
                with st.container(border=True):
                    st.markdown(f"**{cat}**")
                    col_met1, col_met2 = st.columns(2)
                    with col_met1:
                        st.metric("Limite definido", f"R$ {lim:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                    with col_met2:
                        st.metric("Total gasto", f"R$ {gasto:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

                    st.progress(pct)
                    st.caption(f"{pct * 100:.1f}% do limite utilizado")

                    if lim > 0 and gasto > lim:
                        st.error(f"Atenção: Limite ultrapassado em R$ {gasto - lim:,.2f}!")
                    elif pct >= 0.8:
                        st.warning("Atenção: Você está perto do limite (>= 80%).")
                    else:
                        st.success("Gastos dentro do limite.")
    else:
        st.info("Nenhum orçamento configurado.")

# ------------------------------------------------------------------------------------------------------------------------------------ #
# METAS

elif pagina == "Metas":
    st.subheader("Minhas Metas")
    st.write("Cadastre objetivos financeiros e acompanhe quanto você já guardou para cada um.")

    def formatar_reais_meta(numero):
        return "R$ " + f"{numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    if "aviso_metas" in st.session_state:
        st.success(st.session_state.pop("aviso_metas"))

    with st.container(border=True):
        st.write("**Nova Meta Financeira**")

        with st.form("form_meta", border=False):
            nome_meta = st.text_input("Nome da meta", placeholder="Ex.: Viagem, notebook, reserva de emergência")
            descricao_meta = st.text_area("Descrição (opcional)", placeholder="Descreva seu objetivo", height=80)

            col_alvo, col_guardado = st.columns(2)
            with col_alvo:
                valor_alvo = st.number_input(
                    "Valor-alvo (R$)", min_value=0.01, value=None,
                    step=0.01, format="%.2f", placeholder="Informe o valor"
                )
            with col_guardado:
                valor_guardado = st.number_input(
                    "Valor já guardado (R$)", min_value=0.0,
                    value=0.0, step=0.01, format="%.2f"
                )

            prazo_meta = st.date_input(
                "Prazo para alcançar a meta", value=None,
                min_value=date.today(), format="DD/MM/YYYY"
            )
            salvar_meta = st.form_submit_button("Salvar Meta", use_container_width=True)

        if salvar_meta:
            metas_existentes = buscar_metas()
            nome_limpo = nome_meta.strip() if nome_meta else ""
            nome_repetido = any(
                m["nome"].strip().casefold() == nome_limpo.casefold()
                for m in metas_existentes
            )

            if not nome_limpo:
                st.error("Digite um nome para a meta.")
            elif valor_alvo is None:
                st.error("Informe o valor-alvo da meta.")
            elif prazo_meta is None:
                st.error("Selecione o prazo da meta.")
            elif nome_repetido:
                st.warning("Já existe uma meta com esse nome. Use a opção Editar para atualizá-la.")
            else:
                nova_meta = {
                    "nome": nome_limpo,
                    "descricao": descricao_meta.strip(),
                    "valor_alvo": float(valor_alvo),
                    "valor_guardado": float(valor_guardado),
                    "prazo": prazo_meta.isoformat()
                }
                if criar_meta(nova_meta):
                    st.session_state["aviso_metas"] = "Meta cadastrada com sucesso!"
                    st.rerun()
                else:
                    st.error("Erro ao conectar com o servidor.")

    st.subheader("Minhas Metas Cadastradas")
    metas_banco = buscar_metas()

    if not metas_banco:
        st.info("Nenhuma meta cadastrada.")
    else:
        cards = st.columns(2)

        for posicao, meta in enumerate(metas_banco):
            meta_id = meta["_id"]
            with cards[posicao % 2]:
                with st.container(border=True):
                    st.write(f"### {meta['nome']}")
                    if meta.get("descricao"):
                        st.caption(meta["descricao"])

                    alvo = float(meta["valor_alvo"])
                    guardado = float(meta["valor_guardado"])
                    restante = max(alvo - guardado, 0.0)
                    percentual = (guardado / alvo) * 100
                    prazo = date.fromisoformat(meta["prazo"])
                    dias_restantes = (prazo - date.today()).days

                    st.caption(f"Valor-alvo: {formatar_reais_meta(alvo)}")
                    col_guardado_card, col_restante_card = st.columns(2)
                    with col_guardado_card:
                        st.metric("Valor guardado", formatar_reais_meta(guardado))
                    with col_restante_card:
                        st.metric("Falta guardar", formatar_reais_meta(restante))

                    st.progress(min(max(percentual / 100, 0.0), 1.0))
                    st.caption(f"{percentual:.1f}% da meta alcançada")
                    st.caption(f"Prazo: {prazo.strftime('%d/%m/%Y')}")

                    if percentual >= 100:
                        st.success("Meta alcançada! Parabéns!")
                    elif dias_restantes < 0:
                        st.warning("O prazo terminou e a meta ainda não foi alcançada.")
                    elif dias_restantes == 0:
                        st.warning("O prazo termina hoje.")
                    else:
                        st.info(f"Faltam {dias_restantes} dia(s) para o prazo.")

                    col_movimentar, col_editar, col_excluir = st.columns(3)

                    with col_movimentar:
                        with st.popover("Guardar/retirar"):
                            st.write("**Atualizar valor guardado**")
                            with st.form(f"movimentar_meta_{meta_id}"):
                                operacao = st.radio("Operação", ["Adicionar", "Retirar"])
                                valor_movimento = st.number_input(
                                    "Valor (R$)", min_value=0.01,
                                    step=0.01, format="%.2f"
                                )
                                confirmar_movimento = st.form_submit_button("Confirmar")

                            if confirmar_movimento:
                                if operacao == "Retirar" and valor_movimento > guardado:
                                    st.error("Não é possível retirar mais do que o valor guardado.")
                                else:
                                    variacao = valor_movimento if operacao == "Adicionar" else -valor_movimento
                                    novo_saldo = round(guardado + variacao, 2)
                                    if atualizar_valor_meta(meta_id, novo_saldo):
                                        st.session_state["aviso_metas"] = "Valor guardado atualizado!"
                                        st.rerun()
                                    else:
                                        st.error("Erro ao atualizar valor.")

                    with col_editar:
                        with st.popover("Editar"):
                            st.write("**Editar esta meta**")
                            with st.form(f"editar_meta_{meta_id}"):
                                nome_editado = st.text_input("Nome", value=meta["nome"])
                                descricao_editada = st.text_area(
                                    "Descrição (opcional)", value=meta.get("descricao", "")
                                )
                                alvo_editado = st.number_input(
                                    "Valor-alvo (R$)", min_value=0.01,
                                    value=alvo, step=0.01, format="%.2f"
                                )
                                prazo_editado = st.date_input(
                                    "Prazo", value=prazo, format="DD/MM/YYYY"
                                )
                                salvar_edicao = st.form_submit_button("Salvar alterações")

                            if salvar_edicao:
                                nome_limpo = nome_editado.strip()
                                duplicada = any(
                                    outra["_id"] != meta_id
                                    and outra["nome"].strip().casefold() == nome_limpo.casefold()
                                    for outra in metas_banco
                                )
                                if not nome_limpo:
                                    st.error("Digite um nome para a meta.")
                                elif duplicada:
                                    st.error("Já existe outra meta com esse nome.")
                                else:
                                    payload_edicao = {
                                        "nome": nome_limpo,
                                        "descricao": descricao_editada.strip(),
                                        "valor_alvo": float(alvo_editado),
                                        "valor_guardado": guardado,
                                        "prazo": prazo_editado.isoformat()
                                    }
                                    if editar_meta_api(meta_id, payload_edicao):
                                        st.session_state["aviso_metas"] = "Meta atualizada com sucesso!"
                                        st.rerun()
                                    else:
                                        st.error("Erro ao editar meta.")

                    with col_excluir:
                        with st.popover("Excluir"):
                            st.write(f"Deseja realmente excluir a meta **{meta['nome']}**?")
                            if st.button("Confirmar exclusão", key=f"excluir_meta_{meta_id}"):
                                if excluir_meta_api(meta_id):
                                    st.session_state["aviso_metas"] = "Meta excluída com sucesso."
                                    st.rerun()
                                else:
                                    st.error("Erro ao excluir meta.")

# ------------------------------------------------------------------------------------------------------------------------------------ #

elif pagina == "Relatórios":
    st.subheader("Relatórios Financeiros")

elif pagina == "Conversor de Moedas":
    st.subheader("Conversor de Moedas")