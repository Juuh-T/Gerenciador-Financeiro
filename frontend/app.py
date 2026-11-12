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
)
from auth import acesso_autenticado

st.set_page_config(page_title="Gerenciador Financeiro", layout="wide")


#========================================================================================

# usar True apenas para testes locais. Antes de publicar ou entregar o sistema, 
# colocar False, pois esse modo ignora a verificação de autenticação.

# Modo de desenvolvimento
MODO_DESENVOLVIMENTO = False

if not MODO_DESENVOLVIMENTO:
    if not acesso_autenticado():
        st.stop()

#========================================================================================


if "orcamentos" not in st.session_state:
    st.session_state["orcamentos"] = []
if "metas" not in st.session_state:
    st.session_state["metas"] = []

if "pagina_atual" not in st.session_state:
    st.session_state["pagina_atual"] = "Dashboard" 


st.title("💰 Gerenciador Financeiro")
st.write("Controle suas receitas, despesas e metas financeiras em um só lugar")

# ----------------------------------------------------------------------------------------

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

# -------------------------------------------- Dashboard ----------------------------------------------

if pagina == "Dashboard":
    st.subheader("Visão Geral")
    dados = buscar_resumo_dashboard() # adicionei uma "API para buscar funções para ser usada no front"

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

# -------------------------------------------- Transações ----------------------------------------------

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
                    "data": str(data), #está enviando uma string para o banco para não dar erro
                    "observacao": observacao_opcional
                }

                #chamada da função POST para salvar transações
                if criar_transacao(nova_transacao):
                    st.success("Transação salva")
                    st.rerun()
                else:
                    st.error("Erro ao conectar com o servidor")

        transacao_salva = buscar_transacoes()
        # st.write("Dados recebidos da API:", transacao_salva) # <--- Linha temporaria para teste
        if transacao_salva:
            filtro_tipo = st.selectbox(
                "Filtrar por tipo", ["Todos", "Receita", "Despesa"]
            )
            
            df = pd.DataFrame(transacao_salva)
            
            if filtro_tipo != "Todos":
                df = df[df["tipo"] == filtro_tipo]
            if "_id" in df.columns:
                df = df.drop(columns=["_id"])
            if "data" in df.columns:
                df["data"] = pd.to_datetime(df["data"], errors="coerce").dt.strftime("%d/%m/%Y")

            categorias_filtro = sorted(df["categoria"].dropna().unique())
                
            opcoes_categoria = ["Todas"] + list(categorias_filtro)

            filtro_categoria = st.selectbox(
                "Filtrar por categoria",
                opcoes_categoria
            )
            if filtro_categoria != "Todas":
                df = df[df["categoria"] == filtro_categoria]

            st.dataframe(
                df,
                hide_index=True,
                column_config={
                    "descricao": "Descrição",
                    "tipo": "Tipo",
                    "categoria": "Categoria",
                    "data": "Data",
                    "observacao": "Observação",
                    "valor": st.column_config.NumberColumn(
                        "Valor (R$)",
                        alignment="left",
                        format="R$ %.2f"
                    )
                }
            )           

            

        else:
            st.info("Nenhuma Transação Cadastrada")

# -------------------------------------------- Orçamentos ----------------------------------------------

elif pagina == "Orçamentos":
    st.subheader("Controle de Orçamentos")
    st.write("Defina seus limites financeiros e acompanhe o consumo por categoria.")

    def formatar_reais(numero):
        return "R$ " + f"{numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    tab_banco, tab_mensal = st.tabs([
        "Orçamentos salvos no banco",
        "Orçamentos mensais (temporários)",
    ])

    with tab_banco:
        st.caption("Estes orçamentos usam a API FastAPI/MongoDB da sua dupla. O modelo atual recebe categoria e limite, sem mês/ano.")

        with st.container(border=True):
            st.write("**Novo Orçamento no Banco**")
            with st.form("form_orcamento_api", border=False):
                categoria_api = st.selectbox(
                    "Categoria", ["Alimentação", "Transporte", "Saúde", "Educação", "Lazer", "Moradia", "Outros"],
                    key="categoria_orc_api"
                )
                limite_api = st.number_input(
                    "Limite (R$)", min_value=0.01, step=0.01,
                    format="%.2f", key="limite_orc_api"
                )
                salvar_api = st.form_submit_button("Salvar no Banco")

            if salvar_api:
                novo_orcamento_api = {"categoria": categoria_api, "limite": float(limite_api)}
                if criar_orcamento(novo_orcamento_api):
                    st.success(f"Orçamento para {categoria_api} salvo com sucesso!")
                    st.rerun()
                else:
                    st.error("Não foi possível salvar o orçamento no servidor.")

        with st.container(border=True):
            st.write("**Orçamentos Cadastrados no Banco**")
            orcamentos_api = buscar_orcamentos()

            if orcamentos_api:
                cards_api = st.columns(2)
                for posicao, item in enumerate(orcamentos_api):
                    categoria_item = item.get("categoria", "Sem categoria")
                    limite_item = float(item.get("limite") or 0.0)
                    gasto_item = float(item.get("gasto_atual") or 0.0)
                    percentual_item = float(item.get("percentual") or 0.0)
                    # A versão da API enviada usa percentual de 0 a 1.
                    progresso = max(0.0, min(percentual_item, 1.0))

                    with cards_api[posicao % 2]:
                        with st.container(border=True):
                            st.markdown(f"**{categoria_item}**")
                            col_limite, col_gasto = st.columns(2)
                            with col_limite:
                                st.metric("Limite definido", formatar_reais(limite_item))
                            with col_gasto:
                                st.metric("Total gasto", formatar_reais(gasto_item))

                            st.progress(progresso)
                            st.caption(f"{percentual_item * 100:.1f}% do limite utilizado")
                            if limite_item > 0 and gasto_item > limite_item:
                                st.error(f"Limite ultrapassado em {formatar_reais(gasto_item - limite_item)}!")
                            elif percentual_item >= 0.8:
                                st.warning("Atenção: você está perto do limite (80% ou mais).")
                            else:
                                st.success("Gastos dentro do limite.")
            else:
                st.info("Nenhum orçamento encontrado no banco ou a API está indisponível.")

    with tab_mensal:
        st.caption("Esta seção mantém seus orçamentos mensais por mês/ano, enquanto o backend ainda não aceita esses campos.")
        meses = [
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ]
        categorias_orcamento = [
            "Geral (todas as categorias)", "Alimentação", "Transporte",
            "Saúde", "Educação", "Lazer", "Moradia", "Outros"
        ]
        hoje = date.today()

        # Cadastro: um limite por categoria em cada mês/ano.
        with st.container(border=True):
            st.write("**Novo Orçamento**")

            with st.form("form_orcamento", border=False):
                categoria_orc = st.selectbox("Categoria", categorias_orcamento)
                limite = st.number_input(
                    "Limite mensal (R$)", min_value=0.01, step=0.01, format="%.2f"
                )
                col_mes, col_ano = st.columns(2)
                with col_mes:
                    mes = st.selectbox("Mês", meses, index=hoje.month - 1)
                with col_ano:
                    ano = st.number_input(
                        "Ano", min_value=2000, max_value=2100,
                        value=hoje.year, step=1
                    )
                botao_orcamento = st.form_submit_button("Salvar Orçamento")

            if botao_orcamento:
                existente = None
                for orcamento in st.session_state["orcamentos"]:
                    if (orcamento["categoria"] == categoria_orc
                            and orcamento["mes"] == mes
                            and int(orcamento["ano"]) == int(ano)):
                        existente = orcamento
                        break

                if existente is not None:
                    existente["limite"] = float(limite)
                    st.success("Orçamento atualizado com sucesso!")
                else:
                    novo_orcamento = {
                        "categoria": categoria_orc,
                        "limite": float(limite),
                        "mes": mes,
                        "ano": int(ano)
                    }
                    st.session_state["orcamentos"].append(novo_orcamento)
                    st.success("Orçamento cadastrado com sucesso!")

                # Mostrar imediatamente o período que acabou de ser salvo.
                st.session_state["mes_visual_orc"] = mes
                st.session_state["ano_visual_orc"] = int(ano)


        with st.container(border=True):
            st.write("**Meus Orçamentos**")
            col_mes_filtro, col_ano_filtro = st.columns(2)
            with col_mes_filtro:
                mes_visual = st.selectbox(
                    "Mês de visualização", meses,
                    index=hoje.month - 1, key="mes_visual_orc"
                )
            with col_ano_filtro:
                ano_visual = st.number_input(
                    "Ano de visualização", min_value=2000, max_value=2100,
                    value=hoje.year, step=1, key="ano_visual_orc"
                )

            orcamentos_visiveis = [
                orc for orc in st.session_state["orcamentos"]
                if orc["mes"] == mes_visual and int(orc["ano"]) == int(ano_visual)
            ]

            if not orcamentos_visiveis:
                st.info("Nenhum orçamento cadastrado para esse mês e ano.")
            else:
                # Consulta apenas transações reais do backend.
                transacoes_api = buscar_transacoes()
                gastos_por_categoria = None
                gasto_total = None

                if transacoes_api is None:
                    st.warning("Não foi possível consultar as transações. Os gastos não serão calculados.")
                elif not transacoes_api:
                    gastos_por_categoria = {}
                    gasto_total = 0.0
                else:
                    df_gastos = pd.DataFrame(transacoes_api)
                    colunas = {"tipo", "categoria", "valor", "data"}
                    if not colunas.issubset(df_gastos.columns):
                        st.warning("A API retornou transações sem os campos necessários para os cálculos.")
                    else:
                        df_gastos["data"] = pd.to_datetime(df_gastos["data"], errors="coerce")
                        df_gastos["valor"] = pd.to_numeric(
                            df_gastos["valor"], errors="coerce"
                        ).fillna(0)
                        df_gastos["tipo"] = df_gastos["tipo"].astype(str).str.strip().str.casefold()
                        df_gastos = df_gastos[
                            (df_gastos["tipo"] == "despesa")
                            & (df_gastos["data"].dt.month == meses.index(mes_visual) + 1)
                            & (df_gastos["data"].dt.year == int(ano_visual))
                        ]
                        gastos_por_categoria = df_gastos.groupby("categoria")["valor"].sum().to_dict()
                        gasto_total = float(df_gastos["valor"].sum())

                cards = st.columns(2)
                for posicao, orcamento in enumerate(orcamentos_visiveis):
                    with cards[posicao % 2]:
                        with st.container(border=True):
                            categoria_atual = orcamento["categoria"]
                            limite_atual = float(orcamento["limite"])
                            st.markdown(f"**{categoria_atual}**")
                            st.caption(f"{mes_visual} de {int(ano_visual)}")
                            st.metric("Limite definido", formatar_reais(limite_atual))

                            if gastos_por_categoria is None:
                                st.info("Gastos indisponíveis no momento.")
                            else:
                                if categoria_atual == "Geral (todas as categorias)":
                                    gasto = gasto_total
                                else:
                                    gasto = float(gastos_por_categoria.get(categoria_atual, 0.0))

                                percentual = (gasto / limite_atual) * 100
                                st.metric("Total gasto", formatar_reais(gasto))
                                st.progress(min(percentual / 100, 1.0))
                                st.caption(f"{percentual:.1f}% do limite utilizado")

                                if percentual > 100:
                                    st.error("Limite ultrapassado!")
                                elif percentual >= 80:
                                    st.warning("Atenção: você está perto do limite.")
                                else:
                                    st.success("Gastos dentro do limite.")

                            with st.popover("Excluir orçamento"):
                                st.write("Deseja realmente excluir este orçamento?")
                                if st.button(
                                    "Confirmar exclusão",
                                    key=f"excluir_{categoria_atual}_{mes_visual}_{ano_visual}"
                                ):
                                    st.session_state["orcamentos"].remove(orcamento)
                                    st.rerun()

        st.caption("Orçamentos mensais temporários: não são enviados ao MongoDB. A integração de mês e ano ao backend ainda está pendente.")
    

# ----------------------------------------------- Metas -------------------------------------------------

elif pagina == "Metas":
    st.subheader("Minhas Metas")

    st.write("Cadastre objetivos financeiros e acompanhe quanto você já guardou para cada um.")

    # Os valores são informados pelo usuário, não dependem das transações do banco.
    def formatar_reais_meta(numero):
        return "R$ " + f"{numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    # Exibe mensagens depois de atualizar ou excluir uma meta.
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
            nome_limpo = nome_meta.strip()
            nome_repetido = any(
                m["nome"].strip().casefold() == nome_limpo.casefold()
                for m in st.session_state["metas"]
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
                    "id": uuid4().hex,
                    "nome": nome_limpo,
                    "descricao": descricao_meta.strip(),
                    "valor_alvo": float(valor_alvo),
                    "valor_guardado": float(valor_guardado),
                    "prazo": prazo_meta.isoformat()
                }
                st.session_state["metas"].append(nova_meta)
                st.success("Meta cadastrada com sucesso!")

    with st.container(border=True):
        st.write("**Minhas Metas Cadastradas**")

        if not st.session_state["metas"]:
            st.info("Nenhuma meta cadastrada.")
        else:
            cards = st.columns(2)

            for posicao, meta in enumerate(st.session_state["metas"]):
                with cards[posicao % 2]:
                    with st.container(border=True):
                        st.write(f"### {meta['nome']}")
                        if meta["descricao"]:
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
                                with st.form(f"movimentar_meta_{meta['id']}"):
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
                                        meta["valor_guardado"] = round(guardado + variacao, 2)
                                        st.session_state["aviso_metas"] = "Valor guardado atualizado!"
                                        st.rerun()

                        with col_editar:
                            with st.popover("Editar"):
                                st.write("**Editar esta meta**")
                                with st.form(f"editar_meta_{meta['id']}"):
                                    nome_editado = st.text_input("Nome", value=meta["nome"])
                                    descricao_editada = st.text_area(
                                        "Descrição (opcional)", value=meta["descricao"]
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
                                        outra["id"] != meta["id"]
                                        and outra["nome"].strip().casefold() == nome_limpo.casefold()
                                        for outra in st.session_state["metas"]
                                    )
                                    if not nome_limpo:
                                        st.error("Digite um nome para a meta.")
                                    elif duplicada:
                                        st.error("Já existe outra meta com esse nome.")
                                    else:
                                        meta["nome"] = nome_limpo
                                        meta["descricao"] = descricao_editada.strip()
                                        meta["valor_alvo"] = float(alvo_editado)
                                        meta["prazo"] = prazo_editado.isoformat()
                                        st.session_state["aviso_metas"] = "Meta atualizada com sucesso!"
                                        st.rerun()

                        with col_excluir:
                            with st.popover("Excluir"):
                                st.write(f"Deseja realmente excluir a meta **{meta['nome']}**?")
                                if st.button("Confirmar exclusão", key=f"excluir_meta_{meta['id']}"):
                                    st.session_state["metas"].remove(meta)
                                    st.session_state["aviso_metas"] = "Meta excluída com sucesso."
                                    st.rerun()

    st.caption(
        "As metas e os valores guardados ficam apenas nesta sessão do Streamlit. "
        "Eles não são enviados ao MongoDB e não são descontados automaticamente do saldo."
    )

# --------------------------------------------- Relatórios ----------------------------------------------

elif pagina == "Relatórios":
    st.subheader("Relatórios Financeiros")

# ----------------------------------------- Conversor de Moedas ------------------------------------------

elif pagina == "Conversor de Moedas":
    st.subheader("Conversor de Moedas")