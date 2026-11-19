import streamlit as st
import pandas as pd
import altair as alt
import requests
from datetime import datetime
from datetime import date

from api import (
    buscar_transacoes,
    buscar_resumo_dashboard,
    criar_transacao,
    buscar_orcamentos,
    criar_orcamento,
    buscar_metas,
    criar_meta,
    atualizar_valor_meta,
    editar_meta_api,
    excluir_meta_api,
    buscar_relatorio,
    baixar_relatorio_excel,
    baixar_relatorio_pdf,
    editar_transacao,
    excluir_transacao,
    excluir_orcamento,
)
from auth import acesso_autenticado

@st.cache_data(ttl=60)
def buscar_cotacoes():
    url = "https://economia.awesomeapi.com.br/json/last/USD-BRL,EUR-BRL"

    resposta = requests.get(url, timeout=10)
    resposta.raise_for_status()

    return resposta.json()

# ------------------------------------- Auxiliares do Dashboard -----------------------------------------

MESES_ABREV = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
MESES_NOME = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]
# Mesmas cores usadas no gráfico da página de Relatórios
COR_RECEITA = "#22c55e"
COR_DESPESA = "#ef4444"
COR_SALDO = "#3b82f6"


def formatar_moeda(numero):
    sinal = "-" if round(numero, 2) < 0 else ""
    return f"{sinal}R$ " + f"{abs(numero):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def moeda_md(numero):
    """Valor em reais para textos com markdown (o \\$ evita virar fórmula)."""
    return formatar_moeda(numero).replace("$", "\\$")

def eixo_reais(**opcoes):
    """Eixo com rótulos no padrão brasileiro (R$ 1.500)."""
    return alt.Axis(
        title=None,
        labelExpr="'R$ ' + replace(format(datum.value, ',.0f'), regexp(',', 'g'), '.')",
        **opcoes
    )


def preparar_transacoes(transacoes):
    """Converte a lista da API em DataFrame com data, valor e tipo padronizados."""
    colunas_base = ["data", "valor", "tipo", "categoria", "descricao", "chave_mes"]
    if not transacoes:
        return pd.DataFrame(columns=colunas_base)

    df = pd.DataFrame(transacoes)
    if not {"data", "valor", "tipo"}.issubset(df.columns):
        return pd.DataFrame(columns=colunas_base)

    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0.0)
    df["tipo"] = df["tipo"].astype(str).str.strip().str.casefold()
    if "categoria" not in df.columns:
        df["categoria"] = "Outros"
    df["categoria"] = df["categoria"].fillna("Outros")
    if "descricao" not in df.columns:
        df["descricao"] = ""

    df = df.dropna(subset=["data"])
    df["chave_mes"] = df["data"].dt.strftime("%Y-%m")
    return df


def ultimos_meses(referencia: date, quantidade: int):
    """Retorna [(ano, mes), ...] dos últimos meses, do mais antigo ao atual."""
    ano, mes = referencia.year, referencia.month
    lista = []
    for _ in range(quantidade):
        lista.append((ano, mes))
        mes -= 1
        if mes == 0:
            mes, ano = 12, ano - 1
    return list(reversed(lista))


def totais_do_mes(df, chave_mes: str):
    """Retorna (receitas, despesas) de um mês no formato 'AAAA-MM'."""
    if df.empty:
        return 0.0, 0.0
    do_mes = df[df["chave_mes"] == chave_mes]
    receitas = float(do_mes.loc[do_mes["tipo"] == "receita", "valor"].sum())
    despesas = float(do_mes.loc[do_mes["tipo"] == "despesa", "valor"].sum())
    return receitas, despesas


def variacao_moeda(atual: float, anterior: float):
    """Texto da variação para o st.metric (o sinal define a seta)."""
    diferenca = round(atual - anterior, 2)
    if diferenca == 0:
        return "R$ 0,00"
    sinal = "-" if diferenca < 0 else "+"
    return f"{sinal}{formatar_moeda(abs(diferenca))}"


def cor_variacao(delta: str, cor: str = "normal"):
    """Deixa a variação cinza (sem seta colorida) quando não houve mudança."""
    return cor if delta.startswith(("+", "-")) else "off"



st.set_page_config(page_title="Gerenciador Financeiro", layout="wide")

# Modo de desenvolvimento
MODO_DESENVOLVIMENTO = False

if not MODO_DESENVOLVIMENTO:
    if not acesso_autenticado():
        st.stop()


if "orcamentos" not in st.session_state:
    st.session_state["orcamentos"] = []
if "pagina_atual" not in st.session_state:
    st.session_state["pagina_atual"] = "Dashboard"

st.markdown(
    """
    <style>
      .block-container { padding-top: 4rem; }

      /* Cabeçalho no mesmo estilo da tela de login */
      .gf-topo { display: flex; align-items: center; gap: 14px; margin-bottom: 1.4rem; }
      .gf-logo {
          flex-shrink: 0; font-size: 40px; line-height: 1;
          display: flex; align-items: center; justify-content: center;
      }
      .gf-titulo { font-size: 1.6rem; font-weight: 700; line-height: 1.2; }
      .gf-subtitulo { opacity: .65; font-size: .9rem; }

      /* Marca na barra lateral */
      .gf-marca { display: flex; align-items: center; gap: 10px; margin: .3rem 0 .2rem; }
      .gf-marca-nome { font-weight: 700; font-size: 1.05rem; line-height: 1.2; }
      .gf-marca-sub { opacity: .6; font-size: .68rem; letter-spacing: .08em; }

      /* Números dos cards em destaque */
      [data-testid="stMetricValue"] { font-weight: 700; }
      [data-testid="stMetricLabel"] p { opacity: .75; }

      /* Botões de salvar dos formulários em azul */
      [data-testid="stFormSubmitButton"] button {
          background: #2563EB; color: #ffffff; border: none; font-weight: 600;
      }
      [data-testid="stFormSubmitButton"] button:hover {
          background: #1d4ed8; color: #ffffff;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="gf-topo">
      <div class="gf-logo">💰</div>
      <div>
        <div class="gf-titulo">Gerenciador Financeiro</div>
        <div class="gf-subtitulo">Controle suas receitas, despesas e metas financeiras em um só lugar</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown(
    """
    <div class="gf-marca">
      <div>
        <div class="gf-marca-nome">Finanças</div>
        <div class="gf-marca-sub">GERENCIADOR FINANCEIRO</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)
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
    dados = buscar_resumo_dashboard()
    transacoes_dash = buscar_transacoes()
    df_dash = preparar_transacoes(transacoes_dash)

    hoje = date.today()
    (ano_ant, mes_ant), (ano_atual, mes_atual) = ultimos_meses(hoje, 2)
    chave_atual = f"{ano_atual:04d}-{mes_atual:02d}"
    chave_anterior = f"{ano_ant:04d}-{mes_ant:02d}"
    nome_mes_atual = f"{MESES_NOME[mes_atual - 1]} de {ano_atual}"
    texto_comparacao = f"Comparado a {MESES_NOME[mes_ant - 1]} de {ano_ant}"

    if transacoes_dash is None:
        # Sem a lista de transações, mantém os totais calculados pela API.
        receita_mes, despesa_mes = dados["receita_mes"], dados["despesa_mes"]
        receita_ant, despesa_ant = receita_mes, despesa_mes
    else:
        receita_mes, despesa_mes = totais_do_mes(df_dash, chave_atual)
        receita_ant, despesa_ant = totais_do_mes(df_dash, chave_anterior)
    economia_mes = receita_mes - despesa_mes
    economia_ant = receita_ant - despesa_ant

    st.caption(f"Movimentações do mês: {nome_mes_atual}")

    delta_saldo = variacao_moeda(economia_mes, 0)
    delta_receita = variacao_moeda(receita_mes, receita_ant)
    delta_despesa = variacao_moeda(despesa_mes, despesa_ant)
    delta_economia = variacao_moeda(economia_mes, economia_ant)

    col1, col2 = st.columns(2, gap="small")
    with col1:
        st.metric(
            label="Saldo Atual", value=formatar_moeda(dados["saldo_atual"]), border=True,
            delta=delta_saldo, delta_color=cor_variacao(delta_saldo),
            help="Receitas menos despesas de todas as transações. A variação mostra quanto o saldo mudou neste mês."
        )
    with col2:
        st.metric(
            label="Receita do Mês", value=formatar_moeda(receita_mes), border=True,
            delta=delta_receita, delta_color=cor_variacao(delta_receita), help=texto_comparacao
        )

    col3, col4 = st.columns(2, gap="small")
    with col3:
        st.metric(
            label="Despesas do Mês", value=formatar_moeda(despesa_mes), border=True,
            delta=delta_despesa, delta_color=cor_variacao(delta_despesa, "inverse"),
            help=texto_comparacao
        )
    with col4:
        st.metric(
            label="Economia do Mês", value=formatar_moeda(economia_mes), border=True,
            delta=delta_economia, delta_color=cor_variacao(delta_economia), help=texto_comparacao
        )

    # ---------- Gráficos de transações ----------
    if transacoes_dash is None:
        st.warning("Não foi possível carregar as transações. Os gráficos não serão exibidos.")
    elif df_dash.empty:
        with st.container(border=True):
            st.info("Cadastre suas primeiras transações para ver os gráficos do dashboard.")
            st.button(
                "Cadastrar transação", key="dash_ir_transacoes_vazio",
                icon=":material/add:", on_click=navegar, args=("Transações",)
            )
    else:
        col_meses, col_categorias = st.columns([3, 2], gap="small")
        ALTURA_CARDS = 450

        # Receitas vs. Despesas nos últimos 6 meses
        with col_meses:
            with st.container(border=True, height=ALTURA_CARDS):
                st.write("**Receitas vs. Despesas — últimos 6 meses**")

                linhas_meses = []
                for ano, mes in ultimos_meses(hoje, 6):
                    receita, despesa = totais_do_mes(df_dash, f"{ano:04d}-{mes:02d}")
                    rotulo = f"{MESES_ABREV[mes - 1]}/{str(ano)[2:]}"
                    for tipo, valor_tipo in (("Receita", receita), ("Despesa", despesa)):
                        linhas_meses.append({
                            "Mês": rotulo,
                            "Tipo": tipo,
                            "Valor": valor_tipo,
                            "Valor (R$)": formatar_moeda(valor_tipo)
                        })
                df_meses = pd.DataFrame(linhas_meses)
                ordem_meses = list(dict.fromkeys(df_meses["Mês"]))

                grafico_meses = alt.Chart(df_meses).mark_bar(
                    cornerRadiusTopLeft=4, cornerRadiusTopRight=4
                ).encode(
                    x=alt.X("Mês:N", sort=ordem_meses, title=None, axis=alt.Axis(labelAngle=0)),
                    xOffset=alt.XOffset(
                        "Tipo:N", sort=["Receita", "Despesa"], scale=alt.Scale(paddingInner=0.1)
                    ),
                    y=alt.Y("Valor:Q", axis=eixo_reais(tickCount=5)),
                    color=alt.Color(
                        "Tipo:N",
                        scale=alt.Scale(domain=["Receita", "Despesa"], range=[COR_RECEITA, COR_DESPESA]),
                        legend=alt.Legend(title=None, orient="top")
                    ),
                    tooltip=[
                        alt.Tooltip("Mês:N"),
                        alt.Tooltip("Tipo:N"),
                        alt.Tooltip("Valor (R$):N")
                    ]
                ).properties(height=300)
                st.altair_chart(grafico_meses)

        # Despesas do mês atual por categoria
        with col_categorias:
            with st.container(border=True, height=ALTURA_CARDS):
                st.write(f"**Despesas por categoria — {MESES_ABREV[mes_atual - 1]}/{str(ano_atual)[2:]}**")

                despesas_mes = df_dash[
                    (df_dash["tipo"] == "despesa") & (df_dash["chave_mes"] == chave_atual)
                ]
                if despesas_mes.empty:
                    st.info("Nenhuma despesa registrada neste mês.")
                else:
                    df_categorias = (
                        despesas_mes.groupby("categoria")["valor"].sum()
                        .sort_values(ascending=False).reset_index()
                    )
                    df_categorias.columns = ["Categoria", "Valor"]
                    total_despesas_mes = float(df_categorias["Valor"].sum())
                    df_categorias["Valor (R$)"] = df_categorias["Valor"].apply(formatar_moeda)
                    df_categorias["Participação"] = df_categorias["Valor"].apply(
                        lambda v: f"{(v / total_despesas_mes) * 100:.1f}%".replace(".", ",")
                    )

                    grafico_categorias = alt.Chart(df_categorias).mark_bar(
                        cornerRadiusEnd=4, color=COR_DESPESA, size=22
                    ).encode(
                        y=alt.Y("Categoria:N", sort="-x", title=None),
                        x=alt.X("Valor:Q", axis=eixo_reais(tickCount=4)),
                        tooltip=[
                            alt.Tooltip("Categoria:N"),
                            alt.Tooltip("Valor (R$):N"),
                            alt.Tooltip("Participação:N")
                        ]
                    ).properties(height=260)
                    st.altair_chart(grafico_categorias)

                    maior = df_categorias.iloc[0]
                    st.caption(
                        f"Maior gasto: **{maior['Categoria']}** "
                        f"({maior['Valor (R$)']} · {maior['Participação']} do mês)"
                    )

        # Evolução do saldo acumulado
        with st.container(border=True):
            st.write("**Evolução do saldo**")

            movimentos = df_dash[df_dash["tipo"].isin(["receita", "despesa"])].copy()
            movimentos["movimento"] = movimentos["valor"].where(
                movimentos["tipo"] == "receita", -movimentos["valor"]
            )
            df_saldo = (
                movimentos.groupby(movimentos["data"].dt.normalize())["movimento"]
                .sum().sort_index().cumsum().reset_index()
            )
            df_saldo.columns = ["Data", "Saldo"]
            df_saldo["Dia"] = df_saldo["Data"].dt.strftime("%d/%m/%Y")
            df_saldo["Saldo (R$)"] = df_saldo["Saldo"].apply(formatar_moeda)

            linha_saldo = alt.Chart(df_saldo).mark_line(
                strokeWidth=2, color=COR_SALDO,
                point=alt.OverlayMarkDef(size=60, filled=True, color=COR_SALDO)
            ).encode(
                x=alt.X("Data:T", title=None, axis=alt.Axis(format="%d/%m/%y", labelAngle=0)),
                y=alt.Y("Saldo:Q", axis=eixo_reais()),
                tooltip=[alt.Tooltip("Dia:N", title="Data"), alt.Tooltip("Saldo (R$):N", title="Saldo")]
            )
            linha_zero = alt.Chart(pd.DataFrame({"zero": [0]})).mark_rule(
                color="gray", strokeDash=[4, 4], opacity=0.5
            ).encode(y="zero:Q")

            st.altair_chart((linha_zero + linha_saldo).properties(height=280))
            st.caption("Saldo acumulado dia a dia, considerando todas as transações cadastradas.")

    # ---------- Orçamentos e Metas ----------
    col_orc_dash, col_meta_dash = st.columns(2, gap="small")

    with col_orc_dash:
        with st.container(border=True):
            st.write("**Orçamentos**")
            orcamentos_dash = buscar_orcamentos()

            if not orcamentos_dash:
                st.info("Nenhum orçamento cadastrado no banco.")
            else:
                estourados = 0
                for item in orcamentos_dash:
                    categoria_item = item.get("categoria", "Sem categoria")
                    limite_item = float(item.get("limite") or 0.0)
                    gasto_item = float(item.get("gasto_atual") or 0.0)
                    uso = (gasto_item / limite_item) if limite_item > 0 else 0.0

                    if uso > 1:
                        estourados += 1
                        situacao = " · ⛔ Limite ultrapassado"
                    elif uso >= 0.8:
                        situacao = " · ⚠️ Perto do limite"
                    else:
                        situacao = ""

                    st.progress(
                        max(0.0, min(uso, 1.0)),
                        text=(
                            f"**{categoria_item}** · {moeda_md(gasto_item)} de "
                            f"{moeda_md(limite_item)} ({uso * 100:.0f}%){situacao}"
                        )
                    )

                if estourados:
                    st.error(f"{estourados} orçamento(s) com o limite ultrapassado.")

            st.button(
                "Gerenciar orçamentos", key="dash_ir_orcamentos", type="tertiary",
                icon=":material/arrow_forward:", on_click=navegar, args=("Orçamentos",)
            )

    with col_meta_dash:
        with st.container(border=True):
            st.write("**Metas**")
            metas_dash = buscar_metas()

            if not metas_dash:
                st.info("Nenhuma meta cadastrada.")
            else:
                concluidas = 0
                for meta in metas_dash:
                    alvo_meta = float(meta.get("valor_alvo") or 0.0)
                    guardado_meta = float(meta.get("valor_guardado") or 0.0)
                    progresso_meta = (guardado_meta / alvo_meta) if alvo_meta > 0 else 0.0

                    if progresso_meta >= 1:
                        concluidas += 1
                        situacao = " · ✅ Alcançada"
                    else:
                        situacao = ""

                    st.progress(
                        max(0.0, min(progresso_meta, 1.0)),
                        text=(
                            f"**{meta.get('nome', 'Meta')}** · {moeda_md(guardado_meta)} de "
                            f"{moeda_md(alvo_meta)} ({progresso_meta * 100:.0f}%){situacao}"
                        )
                    )

                total_guardado = sum(float(m.get("valor_guardado") or 0.0) for m in metas_dash)
                st.caption(
                    f"{concluidas} de {len(metas_dash)} meta(s) alcançada(s) · "
                    f"Total guardado: {formatar_moeda(total_guardado)}"
                )

            st.button(
                "Gerenciar metas", key="dash_ir_metas", type="tertiary",
                icon=":material/arrow_forward:", on_click=navegar, args=("Metas",)
            )

    # ---------- Últimas transações ----------
    if not df_dash.empty:
        with st.container(border=True):
            st.write("**Últimas transações**")

            colunas_tabela = [
                c for c in ["data", "descricao", "tipo", "categoria", "valor"] if c in df_dash.columns
            ]
            df_ultimas = df_dash.sort_values("data", ascending=False).head(5)[colunas_tabela].copy()
            df_ultimas["data"] = df_ultimas["data"].dt.strftime("%d/%m/%Y")
            df_ultimas["tipo"] = df_ultimas["tipo"].str.capitalize()

            st.dataframe(
                df_ultimas,
                hide_index=True,
                width="stretch",
                column_config={
                    "data": "Data",
                    "descricao": "Descrição",
                    "tipo": "Tipo",
                    "categoria": "Categoria",
                    "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f")
                }
            )
            st.button(
                "Ver todas as transações", key="dash_ir_transacoes", type="tertiary",
                icon=":material/arrow_forward:", on_click=navegar, args=("Transações",)
            )

# -------------------------------------------- Transações ----------------------------------------------

elif pagina == "Transações":
    st.subheader("Minhas Transações")
    if "aviso_transacoes" in st.session_state:
        st.success(st.session_state.pop("aviso_transacoes"))

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
                    "data": str(data),
                    "observacao": observacao_opcional
                }
                if criar_transacao(nova_transacao):
                    st.session_state["aviso_transacoes"] = "Transação salva com sucesso!"
                    st.rerun()
                else:
                    st.error("Erro ao conectar com o servidor")

        transacao_salva = buscar_transacoes()
        if transacao_salva:
            filtro_tipo = st.selectbox("Filtrar por tipo", ["Todos", "Receita", "Despesa"])
            df = pd.DataFrame(transacao_salva)
            
            if filtro_tipo != "Todos":
                df = df[df["tipo"] == filtro_tipo]

            categorias_filtro = sorted(df["categoria"].dropna().unique())
            opcoes_categoria = ["Todas"] + list(categorias_filtro)

            filtro_categoria = st.selectbox("Filtrar por categoria", opcoes_categoria)
            if filtro_categoria != "Todas":
                df = df[df["categoria"] == filtro_categoria]

            # Guarda os IDs da lista filtrada antes de esconder as colunas internas
            ids_filtrados = list(df["_id"]) if "_id" in df.columns else []

            df_exibicao = df.drop(columns=["_id", "user_id"], errors="ignore")
            if "data" in df_exibicao.columns:
                df_exibicao["data"] = pd.to_datetime(
                    df_exibicao["data"], errors="coerce"
                ).dt.strftime("%d/%m/%Y")

            st.dataframe(
                df_exibicao,
                hide_index=True,
                column_config={
                    "descricao": "Descrição",
                    "tipo": "Tipo",
                    "categoria": "Categoria",
                    "data": "Data",
                    "observacao": "Observação",
                    "valor": st.column_config.NumberColumn(
                        "Valor (R$)", alignment="left", format="R$ %.2f"
                    )
                }
            )
        # ---------- Editar / excluir ----------
            with st.container(border=True):
                st.write("**Editar ou excluir uma transação**")

                transacoes_por_id = {t["_id"]: t for t in transacao_salva}
                ids_opcoes = sorted(
                    (i for i in ids_filtrados if i in transacoes_por_id),
                    key=lambda i: str(transacoes_por_id[i].get("data", "")),
                    reverse=True
                )

                def descrever_transacao(transacao_id):
                    t = transacoes_por_id[transacao_id]
                    data_txt = pd.to_datetime(t.get("data"), errors="coerce")
                    data_txt = data_txt.strftime("%d/%m/%Y") if not pd.isna(data_txt) else "Sem data"
                    return (
                        f"{data_txt} · {t.get('descricao', '')} · {t.get('tipo', '')} · "
                        f"{formatar_moeda(float(t.get('valor', 0)))}"
                    )

                if not ids_opcoes:
                    st.info("Nenhuma transação encontrada com os filtros selecionados.")
                else:
                    transacao_id = st.selectbox(
                        "Selecione a transação", ids_opcoes,
                        format_func=descrever_transacao, key="transacao_selecionada"
                    )
                    transacao = transacoes_por_id[transacao_id]

                    try:
                        data_atual = date.fromisoformat(str(transacao.get("data", ""))[:10])
                    except ValueError:
                        data_atual = date.today()

                    col_editar_tr, col_excluir_tr = st.columns(2)

                    with col_editar_tr:
                        with st.popover("Editar"):
                            st.write("**Editar esta transação**")

                            tipo_atual = transacao.get("tipo", "Despesa")
                            tipo_editado = st.selectbox(
                                "Tipo", ["Receita", "Despesa"],
                                index=0 if tipo_atual == "Receita" else 1,
                                key=f"tipo_edit_{transacao_id}"
                            )
                            categorias_edicao = (
                                categorias_receita if tipo_editado == "Receita" else categorias_despesa
                            )
                            categoria_atual = transacao.get("categoria")

                            with st.form(f"editar_transacao_{transacao_id}"):
                                descricao_editada = st.text_input(
                                    "Descrição", value=transacao.get("descricao", ""),
                                    key=f"desc_edit_{transacao_id}"
                                )
                                valor_editado = st.number_input(
                                    "Valor (R$)", min_value=0.01,
                                    value=max(float(transacao.get("valor", 0.01)), 0.01),
                                    step=0.01, format="%.2f", key=f"valor_edit_{transacao_id}"
                                )
                                categoria_editada = st.selectbox(
                                    "Categoria", categorias_edicao,
                                    index=(
                                        categorias_edicao.index(categoria_atual)
                                        if categoria_atual in categorias_edicao else 0
                                    ),
                                    key=f"cat_edit_{transacao_id}_{tipo_editado}"
                                )
                                data_editada = st.date_input(
                                    "Data", value=data_atual, format="DD/MM/YYYY",
                                    key=f"data_edit_{transacao_id}"
                                )
                                observacao_editada = st.text_area(
                                    "Observação (opcional)", value=transacao.get("observacao") or "",
                                    key=f"obs_edit_{transacao_id}"
                                )
                                salvar_transacao = st.form_submit_button("Salvar alterações")

                            if salvar_transacao:
                                if not descricao_editada.strip():
                                    st.error("Digite uma descrição para a transação.")
                                else:
                                    payload_transacao = {
                                        "descricao": descricao_editada.strip(),
                                        "valor": float(valor_editado),
                                        "tipo": tipo_editado,
                                        "categoria": categoria_editada,
                                        "data": data_editada.isoformat(),
                                        "observacao": observacao_editada.strip()
                                    }
                                    if editar_transacao(transacao_id, payload_transacao):
                                        st.session_state["aviso_transacoes"] = "Transação atualizada com sucesso!"
                                        st.rerun()
                                    else:
                                        st.error("Erro ao editar a transação.")

                    with col_excluir_tr:
                        with st.popover("Excluir"):
                            st.write(
                                f"Deseja realmente excluir a transação "
                                f"**{transacao.get('descricao', '')}**?"
                            )
                            st.caption("Essa ação não pode ser desfeita.")
                            if st.button("Confirmar exclusão", key=f"excluir_transacao_{transacao_id}"):
                                if excluir_transacao(transacao_id):
                                    st.session_state.pop("transacao_selecionada", None)
                                    st.session_state["aviso_transacoes"] = "Transação excluída com sucesso."
                                    st.rerun()
                                else:
                                    st.error("Erro ao excluir a transação.")
        else:
            st.info("Nenhuma Transação Cadastrada")

# -------------------------------------------- Orçamentos ----------------------------------------------

elif pagina == "Orçamentos":
    st.subheader("Controle de Orçamentos")
    st.write("Defina seus limites financeiros e acompanhe o consumo por categoria.")
    if "aviso_orcamentos" in st.session_state:
        st.success(st.session_state.pop("aviso_orcamentos"))

    def formatar_reais(numero):
        return "R$ " + f"{numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    tab_banco, tab_mensal = st.tabs([
        "Orçamentos salvos no banco",
        "Orçamentos mensais (temporários)",
    ])

    with tab_banco:
        st.caption("Estes orçamentos usam a API FastAPI/MongoDB. O modelo atual recebe categoria e limite, sem mês/ano.")

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
                    st.session_state["aviso_orcamentos"] = f"Orçamento para {categoria_api} salvo com sucesso!"
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
                            with st.popover("Excluir orçamento"):
                                st.write(f"Deseja realmente excluir o orçamento de **{categoria_item}**?")
                                if st.button("Confirmar exclusão", key=f"excluir_orc_api_{item.get('_id')}"):
                                    if excluir_orcamento(item.get("_id")):
                                        st.session_state["aviso_orcamentos"] = f"Orçamento de {categoria_item} excluído."
                                        st.rerun()
                                    else:
                                        st.error("Erro ao excluir o orçamento.")
            else:
                st.info("Nenhum orçamento encontrado.")

    with tab_mensal:
        st.caption("Esta seção mantém orçamentos mensais por mês/ano na sessão atual.")
        meses = [
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ]
        categorias_orcamento = [
            "Geral (todas as categorias)", "Alimentação", "Transporte",
            "Saúde", "Educação", "Lazer", "Moradia", "Outros"
        ]
        hoje = date.today()

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
                        df_gastos["valor"] = pd.to_numeric(df_gastos["valor"], errors="coerce").fillna(0)
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

# ----------------------------------------------- Metas -------------------------------------------------

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
            salvar_meta = st.form_submit_button("Salvar Meta", width="stretch")

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

    with st.container(border=True):
        st.write("**Minhas Metas Cadastradas**")
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

# --------------------------------------------- Relatórios ----------------------------------------------

elif pagina == "Relatórios":
    st.subheader("Relatórios Financeiros")
    st.write("Analise suas receitas e despesas por período e exporte sua planilha.")

    hoje = date.today()
    inicio_mes = hoje.replace(day=1)

    with st.container(border=True):
        col_ini, col_fim = st.columns(2)
        with col_ini:
            data_inicio = st.date_input("Data inicial", value=inicio_mes, format="DD/MM/YYYY")
        with col_fim:
            data_fim = st.date_input("Data final", value=hoje, format="DD/MM/YYYY")

    if data_inicio > data_fim:
        st.error("A data inicial não pode ser maior que a data final.")
    else:
        relatorio = buscar_relatorio(data_inicio.isoformat(), data_fim.isoformat())

        if relatorio:
            resumo = relatorio["resumo"]
            col1, col2, col3 = st.columns(3)
            col1.metric("Receitas no Período", formatar_moeda(resumo["total_receitas"]), border=True)
            col2.metric("Despesas no Período", formatar_moeda(resumo["total_despesas"]), border=True)
            col3.metric("Saldo do Período", formatar_moeda(resumo["saldo_periodo"]), border=True)

            with st.container(border=True):
                st.write("**Receitas vs. Despesas no Período**")
                if relatorio["grafico"]:
                    df_graf = pd.DataFrame(relatorio["grafico"])
                    df_graf["data"] = pd.to_datetime(df_graf["data"]).dt.strftime("%d/%m/%Y")
                    df_graf = df_graf.set_index("data")
                    st.bar_chart(
                        df_graf[["Receita", "Despesa"]],
                        color=["#22c55e", "#ef4444"],
                        stack=False
                    )
                else:
                    st.info("Nenhuma movimentação encontrada para gerar o gráfico neste período.")

            with st.container(border=True):
                st.write("**Detalhamento das Transações**")
                if relatorio["transacoes"]:
                    df_tabela = pd.DataFrame(relatorio["transacoes"])
                    if "_id" in df_tabela.columns:
                        df_tabela = df_tabela.drop(columns=["_id", "user_id"], errors="ignore")
                    if "data" in df_tabela.columns:
                        df_tabela["data"] = pd.to_datetime(df_tabela["data"]).dt.strftime("%d/%m/%Y")

                    st.dataframe(
                        df_tabela,
                        hide_index=True,
                        width="stretch",
                        column_config={
                            "descricao": "Descrição",
                            "tipo": "Tipo",
                            "categoria": "Categoria",
                            "data": "Data",
                            "observacao": "Observação",
                            "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f")
                        }
                    )

                    col_btn_excel, col_btn_pdf = st.columns(2)
                    with col_btn_excel:
                        arquivo_excel = baixar_relatorio_excel(data_inicio.isoformat(), data_fim.isoformat())
                        if arquivo_excel:
                            st.download_button(
                                label="📥 Baixar Planilha em Excel (.xlsx)",
                                data=arquivo_excel,
                                file_name=f"relatorio_{data_inicio}_{data_fim}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                width="stretch"
                            )
                    with col_btn_pdf:
                        arquivo_pdf = baixar_relatorio_pdf(data_inicio.isoformat(), data_fim.isoformat())
                        if arquivo_pdf:
                            st.download_button(
                                label="📄 Baixar Relatório em PDF (.pdf)",
                                data=arquivo_pdf,
                                file_name=f"relatorio_{data_inicio}_{data_fim}.pdf",
                                mime="application/pdf",
                                width="stretch"
                            )
                else:
                    st.info("Nenhuma transação registrada entre as datas selecionadas.")

# ----------------------------------------- Conversor de Moedas ------------------------------------------

elif pagina == "Conversor de Moedas":
    st.subheader("Conversor de Moedas")

    st.markdown("""
        <style>
        /* Títulos dos cards */
        [data-testid="stMetricLabel"] p {
            font-size: 18px !important;
            font-weight: 500 !important;
        }

        /* Datas e textos informativos */
        [data-testid="stCaptionContainer"] p {
            font-size: 16px !important;
        }

        /* Nomes dos campos: De, Para e Valor */
        [data-testid="stWidgetLabel"] p {
            font-size: 17px !important;
        }
        </style>
        """, unsafe_allow_html=True)


    if "moeda_origem" not in st.session_state:
        st.session_state["moeda_origem"] = "BRL"
    if "moeda_destino" not in st.session_state:
        st.session_state["moeda_destino"] = "USD"

    col1, col_inverter, col2 = st.columns(
        [4, 1, 4],
        gap="small",
        vertical_alignment="bottom"
    )
    
    def inverter_moedas():
            origem_atual = st.session_state["moeda_origem"]
    
            st.session_state["moeda_origem"] = st.session_state["moeda_destino"]
            st.session_state["moeda_destino"] = origem_atual
    
    with col1:
        moeda_origem = st.selectbox("De", ["BRL", "USD", "EUR"], key="moeda_origem")
    with col_inverter:
        st.button(
            "⇄",
            key="botao_inverter",
            help="Inverter moedas",
            on_click=inverter_moedas,
            type="tertiary",
            width="stretch"
        )
        st.markdown("""
            <style>
            .st-key-botao_inverter button {
                transform: translateY(20px);
                border: none !important;
                background: transparent !important;
                box-shadow: none !important;
                min-height: 54px !important;
            }

            .st-key-botao_inverter button p {
                font-size: 38px !important;
                line-height: 1 !important;
            }
            </style>
            """, unsafe_allow_html=True)
    with col2:
        moeda_destino = st.selectbox("Para", ["BRL", "USD", "EUR"], key="moeda_destino")

    valor = st.number_input(
        "Valor que deseja converter", min_value=0.0, value=0.0, step=0.01, format="%.2f"
    )

    if st.button(
        "Atualizar cotações",
        icon=":material/refresh:",
        key="atualizar_cotacoes"
    ):
        buscar_cotacoes.clear()    

    try:
        dados_moedas = buscar_cotacoes()
 
        cotacao_dolar = float(dados_moedas["USDBRL"]["bid"])
        cotacao_euro = float(dados_moedas["EURBRL"]["bid"])

        data_dolar = dados_moedas["USDBRL"]["create_date"]
        data_euro = dados_moedas["EURBRL"]["create_date"]

        data_dolar_formatada = datetime.fromisoformat(data_dolar).strftime("%d/%m/%Y às %H:%M")
        data_euro_formatada = datetime.fromisoformat(data_euro).strftime("%d/%m/%Y às %H:%M")
 
        cotacoes = {
            "BRL": 1.0,
            "USD": cotacao_dolar,
            "EUR": cotacao_euro
        }

        resultado = valor * cotacoes[moeda_origem] / cotacoes[moeda_destino]
        taxa_conversao = cotacoes[moeda_origem] / cotacoes[moeda_destino]
        taxa_formatada = f"{taxa_conversao:,.4f}".replace(",", "X").replace(".", ",").replace("X", ".")

        simbolos = {
            "BRL": "R$",
            "USD": "US$",
            "EUR": "€"
        }
        simbolo_destino = simbolos[moeda_destino]
        resultado_formatado = f"{resultado:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        with st.container(border=True):
            st.metric(
                "Resultado da conversão",
                f"{simbolo_destino} {resultado_formatado}"
            )
            st.caption(f"1 {moeda_origem} = {taxa_formatada} {moeda_destino}")

        col_dolar, col_euro = st.columns(2, gap="small")

        with col_dolar:
            with st.container(border=True):
                st.metric(
                    label="Cotação do Dólar (USD/BRL)",
                    value=f"R$ {cotacao_dolar:.4f}".replace(".", ",")
                )
                st.caption(f"Última atualização: {data_dolar_formatada}")

        with col_euro:
            with st.container(border=True):
                st.metric(
                    label="Cotação do Euro (EUR/BRL)",
                    value=f"R$ {cotacao_euro:.4f}".replace(".", ",")
                )
                st.caption(f"Última atualização: {data_euro_formatada}")
        
        st.info(
            "Os valores apresentados são estimativas baseadas nas cotações "
            "disponibilizadas pela AwesomeAPI. A conversão não inclui "
            "taxas bancárias, impostos ou tarifas adicionais.",
            icon=":material/info:")

    except (requests.exceptions.RequestException, ValueError, KeyError, TypeError, ZeroDivisionError):
        st.error("Não foi possível consultar ou calcular as cotações. Tente novamente.")