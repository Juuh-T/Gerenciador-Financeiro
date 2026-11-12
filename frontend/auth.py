from datetime import date
import re

import requests
import streamlit as st

from api import API_URL

def _estilos():
    st.markdown(
        """
        <style>
          /* Esconde o menu lateral somente na área pública de autenticação. */
          [data-testid="stSidebar"], [data-testid="collapsedControl"] {
              display: none;
          }
          /* Mais espaço no alto e centro da pagina */
          .block-container { padding-top: clamp(2.5rem, 7vh, 5rem); padding-bottom: 2rem; }
          .gf-identidade {
              display: flex; align-items: center; justify-content: center;
              gap: 12px; margin-bottom: 22px;
          }
          .gf-logo {
              background: #1d3555; color: #93c5fd;
              border-radius: 14px; width: 52px; height: 52px;
              display: flex; align-items: center; justify-content: center;
              font-size: 27px;
          }
          .gf-nome { font-size: 1.2rem; font-weight: 700; line-height: 1.35; }
          .gf-slogan { opacity: .65; font-size: .78rem; }
          .gf-rodape { text-align: center; opacity: .6;
                        font-size: .75rem; margin-top: 1.2rem; }

          .st-key-auth_acoes_login [data-testid="stVerticalBlock"] {
            gap: 0.4rem !important;
        }

        .auth-divisoria {
            border-top: 1px solid rgba(148, 163, 184, 0.28);
            margin-top: -0.45rem;
            padding-top: 0.9rem;
            padding-bottom: 0.7rem;
            text-align: center;
            line-height: 1.4;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def _rodape():
    st.markdown(
        '<div class="gf-rodape">🔒 Acesso à sua conta · © 2026 Gerenciador Financeiro</div>',
        unsafe_allow_html=True,
    )

def _mudar_tela(tela: str):
    st.session_state["auth_tela"] = tela


def sair_da_conta():
    st.session_state.pop("auth_token", None)
    st.session_state.pop("auth_nome", None)
    st.session_state["auth_tela"] = "login"
    st.rerun()

def _cpf_valido(cpf: str) -> bool:
    numeros = re.sub(r"\D", "", cpf)
    if len(numeros) != 11 or len(set(numeros)) == 1:
        return False
    for quantidade in (9, 10):
        soma = sum(int(numeros[i]) * (quantidade + 1 - i) for i in range(quantidade))
        digito = (soma * 10) % 11
        if digito == 10:
            digito = 0
        if digito != int(numeros[quantidade]):
            return False
    return True


def _telefone_valido(telefone: str) -> bool:
    numeros = re.sub(r"\D", "", telefone)
    return len(numeros) in (10, 11)


def _email_valido(email: str) -> bool:
    return bool(re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email))


def _enviar(endpoint: str, dados: dict):
    """Retorna (resposta_json, mensagem_de_erro); nunca registra a senha."""
    try:
        resposta = requests.post(
            f"{API_URL.rstrip('/')}{endpoint}", json=dados, timeout=12
        )
    except requests.RequestException:
        return None, "Não foi possível conectar ao backend. Confira se o FastAPI está rodando."

    if resposta.status_code == 404:
        return None, f"A rota {endpoint} ainda não existe no backend. A interface já está pronta!"
    if resposta.status_code == 401:
        return None, "E-mail ou senha incorretos."
    if resposta.status_code == 409:
        return None, "Já existe uma conta com esses dados."
    if not 200 <= resposta.status_code < 300:
        return None, f"Não foi possível concluir a operação (HTTP {resposta.status_code})."

    try:
        return resposta.json(), None
    except ValueError:
        return {}, None

# -------------------------------------- Tela 1 — Login ---------------------------------------

def mostrar_login():
    with st.container(horizontal_alignment="center"):
        with st.container(border=True, width=640):
            st.markdown("### Bem-vindo de volta!")
            st.caption("Entre na sua conta para continuar de onde parou.")

            if st.session_state.pop("auth_cadastro_concluido", False):
                st.success("Conta criada! Agora você já pode entrar.")

            with st.form("formulario_login", border=False):
                email = st.text_input(
                    "E-mail", placeholder="seu@email.com", icon=":material/mail:"
                )
                senha = st.text_input(
                    "Senha", type="password", placeholder="Digite sua senha",
                    icon=":material/lock:"
                )
                entrar = st.form_submit_button(
                    "Entrar na minha conta", type="primary", width="stretch",
                    icon=":material/arrow_forward:"
                )

            if entrar:
                if not _email_valido(email.strip()) or not senha:
                    st.error("Preencha um e-mail válido e sua senha.")
                else:
                    resultado, erro = _enviar(
                        "/auth/login",
                        {"email": email.strip().lower(), "senha": senha},
                    )
                    if erro:
                        st.error(erro)
                    elif not isinstance(resultado, dict) or not resultado.get("access_token"):
                        st.error("O backend não retornou o token de autenticação esperado.")
                    else:
                        st.session_state["auth_token"] = resultado["access_token"]
                        usuario = resultado.get("usuario") or {}
                        st.session_state["auth_nome"] = (
                            usuario.get("nome", "Minha conta")
                            if isinstance(usuario, dict) else "Minha conta"
                        )
                        st.rerun()

            # Rodapé do Login: 10px de intervalo entre os elementos,
            # mantendo apenas uma linha divisória fina.
            with st.container(key="auth_acoes_login"):
                if st.button("Esqueceu sua senha?", type="tertiary", width="stretch"):
                    st.info("A recuperação de senha será adicionada quando o backend estiver pronto.")

                st.markdown(
                    '<div class="auth-divisoria">Ainda não tem uma conta?</div>',
                    unsafe_allow_html=True,
                )
                st.button(
                    "Criar conta", key="abrir_cadastro", width="stretch",
                    on_click=_mudar_tela, args=("cadastro",),
                    icon=":material/person_add:"
                )
        _rodape()
 
# --------------------------------------- Tela 2 — Cadastro --------------------------------------

def mostrar_cadastro():
    with st.container(horizontal_alignment="center"):
        
        with st.container(border=True, width=700):
            st.markdown("### Crie sua conta")
            st.caption("Preencha seus dados para começar a organizar suas finanças.")

            with st.form("formulario_cadastro", border=False):
                nome = st.text_input(
                    "Nome completo", placeholder="Seu nome completo",
                    icon=":material/person:"
                )
                col_tel, col_cpf = st.columns(2)
                with col_tel:
                    telefone = st.text_input(
                        "Telefone", placeholder="(00) 00000-0000",
                        max_chars=16
                    )
                with col_cpf:
                    cpf = st.text_input(
                        "CPF", placeholder="000.000.000-00", max_chars=14
                    )

                email = st.text_input(
                    "E-mail", placeholder="seu@email.com", icon=":material/mail:"
                )
                nascimento = st.date_input(
                    "Data de nascimento", value=None,
                    min_value=date(1900, 1, 1), max_value=date.today(),
                    format="DD/MM/YYYY"
                )
                col_senha, col_confirma = st.columns(2)
                with col_senha:
                    senha = st.text_input(
                        "Senha", type="password", placeholder="Crie uma senha"
                    )
                with col_confirma:
                    confirmar_senha = st.text_input(
                        "Confirmar senha", type="password",
                        placeholder="Repita sua senha"
                    )
                st.caption("Use uma senha exclusiva, com pelo menos 8 caracteres.")
                cadastrar = st.form_submit_button(
                    "Criar minha conta", type="primary", width="stretch",
                    icon=":material/person_add:"
                )

            if cadastrar:
                if len(nome.strip().split()) < 2:
                    st.error("Informe seu nome completo.")
                elif not _telefone_valido(telefone):
                    st.error("Digite um telefone com DDD válido (10 ou 11 dígitos).")
                elif not _cpf_valido(cpf):
                    st.error("Digite um CPF válido.")
                elif not _email_valido(email.strip()):
                    st.error("Digite um e-mail válido.")
                elif nascimento is None:
                    st.error("Informe sua data de nascimento.")
                elif len(senha) < 8:
                    st.error("A senha deve ter pelo menos 8 caracteres.")
                elif senha != confirmar_senha:
                    st.error("A senha e a confirmação precisam ser iguais.")
                else:
                    payload = {
                        "nome": nome.strip(),
                        "telefone": re.sub(r"\D", "", telefone),
                        "cpf": re.sub(r"\D", "", cpf),
                        "email": email.strip().lower(),
                        "data_nascimento": nascimento.isoformat(),
                        "senha": senha,
                    }
                    _, erro = _enviar("/auth/register", payload)
                    if erro:
                        st.error(erro)
                    else:
                        st.session_state["auth_cadastro_concluido"] = True
                        st.session_state["auth_tela"] = "login"
                        st.rerun()

            st.divider()
            if st.button(
                "Já tem uma conta? Entrar", key="ir_ao_login", width="stretch",
                on_click=_mudar_tela, args=("login",)
            ):
                pass
        st.button(
                    "Voltar para o login", key="voltar_login", type="tertiary",
                    on_click=_mudar_tela, args=("login",),
                    icon=":material/arrow_back:"
                )
        _rodape()

# -------------------- Entrada que o app.py chama antes de exibir o Dashboard --------------------

def acesso_autenticado() -> bool:
    """Exibe o login/cadastro se necessário. Retorna True somente após login via API."""
    if st.session_state.get("auth_token"):
        with st.sidebar:
            st.caption(f"👤 {st.session_state.get('auth_nome', 'Minha conta')}")
            st.button(
                "Sair da conta", width="stretch", key="sair_conta",
                on_click=sair_da_conta, icon=":material/logout:"
            )
        return True

    _estilos()
    if "auth_tela" not in st.session_state:
        st.session_state["auth_tela"] = "login"

    if st.session_state["auth_tela"] == "cadastro":
        mostrar_cadastro()
    else:
        mostrar_login()
    return False