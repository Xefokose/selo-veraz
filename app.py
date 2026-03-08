import streamlit as st
import hashlib
import json
from datetime import datetime
from github import Github, GithubException
import requests
import qrcode
from io import BytesIO

# ============================================
# CONFIGURAÇÃO INICIAL
# ============================================

APP_NAME = "Selo Veraz"
APP_TAGLINE = "A verdade tem marca."
DEFAULT_REPO_NAME = "selo-veraz-registros"
SELOS_DIR = "selos"

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🏷️",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items={"About": f"{APP_NAME} © 2026 - {APP_TAGLINE}"}
)

# ============================================
# CSS
# ============================================

st.markdown("""
<style>
    .selo-card {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
        padding: 2rem;
        border-radius: 18px;
        color: white;
        text-align: center;
        margin: 1.5rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .selo-badge {
        background: #00c853;
        color: white;
        padding: 6px 16px;
        border-radius: 999px;
        font-weight: bold;
        display: inline-block;
        margin: 10px 0;
    }
    .status-verified {
        background: #00c853;
        color: white;
        padding: 10px 20px;
        border-radius: 10px;
        font-weight: bold;
        font-size: 1.1rem;
        text-align: center;
    }
    .status-tampered {
        background: #ff5252;
        color: white;
        padding: 10px 20px;
        border-radius: 10px;
        font-weight: bold;
        font-size: 1.1rem;
        text-align: center;
    }
    .status-notfound {
        background: #ff9800;
        color: white;
        padding: 10px 20px;
        border-radius: 10px;
        font-weight: bold;
        font-size: 1.1rem;
        text-align: center;
    }
    .verification-box {
        background: #f5f5f5;
        color: #111;
        padding: 20px;
        border-radius: 12px;
        margin: 20px 0;
        border-left: 5px solid #1e3a5f;
    }
    .mini-muted {
        opacity: 0.88;
        font-size: 0.92rem;
    }
    .public-box {
        background: #eef7ff;
        color: #111;
        padding: 16px;
        border-radius: 12px;
        border-left: 5px solid #1976d2;
        margin: 15px 0;
    }
    .cert-box {
        background: linear-gradient(180deg, #ffffff 0%, #f6f9fc 100%);
        color: #111;
        padding: 24px;
        border-radius: 18px;
        border: 1px solid #dbe3ea;
        margin: 20px 0;
        box-shadow: 0 8px 24px rgba(0,0,0,0.06);
    }
    .cert-title {
        font-size: 1.4rem;
        font-weight: 700;
        margin-bottom: 6px;
    }
    .cert-subtitle {
        font-size: 0.95rem;
        color: #46515c;
        margin-bottom: 18px;
    }
    .cert-line {
        padding: 10px 0;
        border-bottom: 1px solid #e7edf2;
    }
    .hash-box {
        background: #0f172a;
        color: #e2e8f0;
        padding: 14px;
        border-radius: 10px;
        font-family: monospace;
        font-size: 0.9rem;
        overflow-wrap: break-word;
        margin-top: 10px;
    }
    .badge-code {
        background: #111827;
        color: #e5e7eb;
        padding: 12px;
        border-radius: 10px;
        font-family: monospace;
        font-size: 0.9rem;
        overflow-wrap: break-word;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# SESSION STATE
# ============================================

if "selos_gerados" not in st.session_state:
    st.session_state["selos_gerados"] = 0

if "verificacoes_feitas" not in st.session_state:
    st.session_state["verificacoes_feitas"] = 0

# ============================================
# SECRETS / CONFIG
# ============================================

github_token = st.secrets["GITHUB_TOKEN"] if "GITHUB_TOKEN" in st.secrets else ""
github_username = st.secrets["GITHUB_USERNAME"] if "GITHUB_USERNAME" in st.secrets else ""
github_repo_name = st.secrets["GITHUB_REPO"] if "GITHUB_REPO" in st.secrets else DEFAULT_REPO_NAME
app_base_url = st.secrets["APP_BASE_URL"] if "APP_BASE_URL" in st.secrets else "http://localhost:8501"

# ============================================
# FUNÇÕES UTILITÁRIAS
# ============================================

def gerar_hash_conteudo(conteudo: str) -> str:
    return hashlib.sha256(conteudo.encode("utf-8")).hexdigest()


def gerar_metadados(conteudo: str, autor: str, tipo: str, hash_value: str) -> dict:
    agora = datetime.utcnow().isoformat() + "Z"
    return {
        "id": hash_value,
        "hash": hash_value,
        "autor": autor.strip() if autor.strip() else "Anônimo",
        "tipo": tipo,
        "data_criacao_utc": agora,
        "tamanho_bytes": len(conteudo.encode("utf-8")),
        "versao": "1.2.0",
        "plataforma": APP_NAME
    }


def montar_nome_arquivo(hash_value: str) -> str:
    return f"{SELOS_DIR}/{hash_value}.json"


def get_github_client(token: str):
    try:
        g = Github(token)
        user = g.get_user()
        _ = user.login
        return g, user, None
    except GithubException as e:
        return None, None, f"❌ Token inválido ou expirado. Erro: {str(e)}"
    except Exception as e:
        return None, None, f"❌ Erro de conexão com GitHub: {str(e)}"


def get_repo(user, repo_name: str):
    try:
        repo = user.get_repo(repo_name)
        return repo, None
    except GithubException as e:
        return None, str(e)


def get_or_create_repo(user, repo_name: str = DEFAULT_REPO_NAME):
    try:
        try:
            repo = user.get_repo(repo_name)
            return repo, f"✅ Usando repositório existente: {repo_name}"
        except GithubException:
            repo = user.create_repo(
                name=repo_name,
                description="🏷️ Registros imutáveis do Selo Veraz",
                private=False,
                auto_init=True
            )
            return repo, f"✅ Repositório criado: {repo_name}"
    except GithubException as e:
        return None, f"❌ Erro ao criar/obter repositório: {str(e)}"


def garantir_pasta_selos(repo):
    try:
        repo.get_contents(SELOS_DIR)
        return True, None
    except Exception:
        try:
            repo.create_file(
                path=f"{SELOS_DIR}/.gitkeep",
                message="📁 Cria pasta selos/",
                content="# Pasta para armazenar selos Veraz\n"
            )
            return True, None
        except Exception as e:
            return False, f"Erro ao criar pasta selos/: {str(e)}"


def gerar_links_publicos(hash_value: str, username: str, repo_name: str):
    filename = montar_nome_arquivo(hash_value)
    raw_url = f"https://raw.githubusercontent.com/{username}/{repo_name}/main/{filename}"
    blob_url = f"https://github.com/{username}/{repo_name}/blob/main/{filename}"
    return {
        "raw_url": raw_url,
        "blob_url": blob_url
    }


def gerar_link_verificacao(hash_value: str):
    base = app_base_url.rstrip("/")
    return f"{base}/?hash={hash_value}"


def gerar_badge_html(hash_value: str):
    verify_url = gerar_link_verificacao(hash_value)
    return f'<a href="{verify_url}" target="_blank" rel="noopener noreferrer">✅ Verificado por Selo Veraz</a>'


def gerar_qr_code_bytes(texto: str):
    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=4
    )
    qr.add_data(texto)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.getvalue()


def gerar_certificado_publico(metadados: dict, link_verificacao: str):
    certificado = {
        "selo_veraz": {
            "status": "verificado",
            "tagline": APP_TAGLINE,
            "id": metadados.get("id"),
            "hash": metadados.get("hash"),
            "autor": metadados.get("autor"),
            "tipo": metadados.get("tipo"),
            "data_criacao_utc": metadados.get("data_criacao_utc"),
            "tamanho_bytes": metadados.get("tamanho_bytes"),
            "versao": metadados.get("versao"),
            "plataforma": metadados.get("plataforma"),
            "link_verificacao": link_verificacao
        }
    }
    return certificado


def commit_selo_github(repo, hash_value: str, metadados: dict):
    try:
        sucesso, erro = garantir_pasta_selos(repo)
        if not sucesso:
            return {"success": False, "error": erro}

        filename = montar_nome_arquivo(hash_value)
        arquivo_conteudo = json.dumps(metadados, indent=2, ensure_ascii=False)

        try:
            existing = repo.get_contents(filename)
            repo.update_file(
                path=filename,
                message=f"🏷️ Atualiza Selo Veraz: {metadados['tipo']} - {metadados['autor']}",
                content=arquivo_conteudo,
                sha=existing.sha
            )
        except GithubException:
            repo.create_file(
                path=filename,
                message=f"🏷️ Novo Selo Veraz: {metadados['tipo']} - {metadados['autor']}",
                content=arquivo_conteudo
            )

        commits = repo.get_commits(path=filename)
        ultimo_commit = commits[0]

        return {
            "success": True,
            "commit_url": ultimo_commit.html_url,
            "repo_url": repo.html_url,
            "filename": filename,
            "file_url": f"{repo.html_url}/blob/main/{filename}"
        }
    except Exception as e:
        return {"success": False, "error": f"Erro ao fazer commit: {str(e)}"}


def buscar_selo_por_hash_autenticado(repo, hash_value: str):
    try:
        filename = montar_nome_arquivo(hash_value)
        contents = repo.get_contents(filename)
        conteudo_json = json.loads(contents.decoded_content.decode("utf-8"))

        historico = []
        try:
            commits = list(repo.get_commits(path=filename))
            for commit in commits[:10]:
                historico.append({
                    "data": commit.commit.author.date.isoformat(),
                    "mensagem": commit.commit.message,
                    "url": commit.html_url
                })
        except Exception:
            historico = []

        return {
            "encontrado": True,
            "metadados": conteudo_json,
            "historico": historico,
            "arquivo_url": f"{repo.html_url}/blob/main/{filename}"
        }
    except GithubException:
        return {"encontrado": False, "mensagem": "Hash não registrado no sistema"}
    except Exception as e:
        return {"encontrado": False, "mensagem": f"Erro na busca: {str(e)}"}


def buscar_selo_por_hash_publico(hash_value: str, username: str, repo_name: str):
    try:
        links = gerar_links_publicos(hash_value, username, repo_name)
        response = requests.get(links["raw_url"], timeout=15)

        if response.status_code == 200:
            conteudo_json = response.json()
            return {
                "encontrado": True,
                "metadados": conteudo_json,
                "arquivo_url": links["blob_url"],
                "raw_url": links["raw_url"]
            }

        if response.status_code == 404:
            return {
                "encontrado": False,
                "mensagem": "Hash não encontrado no registro público"
            }

        return {
            "encontrado": False,
            "mensagem": f"Erro público ao consultar GitHub: HTTP {response.status_code}"
        }
    except Exception as e:
        return {
            "encontrado": False,
            "mensagem": f"Erro na verificação pública: {str(e)}"
        }


def exibir_resultado_verificacao_publica(resultado: dict):
    if resultado["encontrado"]:
        st.markdown("""
        <div class="verification-box">
            <div class="status-verified">✅ CONTEÚDO VERIFICADO</div>
            <p>Este hash está registrado publicamente no Selo Veraz.</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 📦 Metadados públicos")
        st.json(resultado["metadados"])

        col1, col2 = st.columns(2)
        with col1:
            if resultado.get("arquivo_url"):
                st.link_button("📄 Ver JSON público", resultado["arquivo_url"], use_container_width=True)
        with col2:
            if resultado.get("raw_url"):
                st.link_button("🌐 Ver RAW público", resultado["raw_url"], use_container_width=True)
    else:
        st.markdown("""
        <div class="verification-box">
            <div class="status-notfound">⚠️ NÃO ENCONTRADO</div>
            <p>Este hash não foi encontrado no registro público.</p>
        </div>
        """, unsafe_allow_html=True)

        st.caption(resultado.get("mensagem", "Nenhuma informação adicional."))


def exibir_certificado_visual(metadados: dict, link_verificacao: str):
    hash_value = metadados.get("hash", "")
    hash_curto = f"{hash_value[:12]}...{hash_value[-12:]}" if len(hash_value) > 24 else hash_value

    st.markdown(f"""
    <div class="cert-box">
        <div class="cert-title">🏷️ Certificado Selo Veraz</div>
        <div class="cert-subtitle">{APP_TAGLINE}</div>

        <div class="cert-line"><strong>Status:</strong> Verificado</div>
        <div class="cert-line"><strong>Autor:</strong> {metadados.get("autor", "Anônimo")}</div>
        <div class="cert-line"><strong>Tipo:</strong> {metadados.get("tipo", "N/D")}</div>
        <div class="cert-line"><strong>Data UTC:</strong> {metadados.get("data_criacao_utc", "N/D")}</div>
        <div class="cert-line"><strong>Tamanho:</strong> {metadados.get("tamanho_bytes", 0)} bytes</div>
        <div class="cert-line"><strong>Versão:</strong> {metadados.get("versao", "N/D")}</div>
        <div class="cert-line"><strong>Hash resumido:</strong> {hash_curto}</div>

        <div style="margin-top: 16px;"><strong>Link de verificação:</strong></div>
        <div class="hash-box">{link_verificacao}</div>

        <div style="margin-top: 16px;"><strong>Hash completo:</strong></div>
        <div class="hash-box">{hash_value}</div>
    </div>
    """, unsafe_allow_html=True)

# ============================================
# QUERY PARAMS
# ============================================

query_hash = ""
try:
    if "hash" in st.query_params:
        query_hash = str(st.query_params["hash"]).strip()
except Exception:
    query_hash = ""

# ============================================
# SIDEBAR
# ============================================

st.sidebar.markdown(f"### 🏷️ {APP_NAME}")
page = st.sidebar.radio(
    "Navegação:",
    ["🔐 Gerar Selo", "🔍 Verificar Selo", "📊 Meus Selos"],
    index=1 if query_hash else 0
)

with st.sidebar:
    st.markdown("---")
    st.markdown("### 🔑 Configuração GitHub")

    if github_token:
        st.success("✅ Token GitHub configurado")
    else:
        github_token = st.text_input("Token GitHub:", type="password")

    if github_username:
        st.info(f"👤 Usuário: {github_username}")
    else:
        github_username = st.text_input("Usuário GitHub público:")

    st.markdown("---")
    st.markdown("### 🌐 App")
    st.caption(app_base_url)

    st.markdown("---")
    st.markdown("### 📊 Estatísticas")
    st.metric("Selos Gerados", st.session_state["selos_gerados"])
    st.metric("Verificações", st.session_state["verificacoes_feitas"])

# ============================================
# PÁGINA 1 — GERAR SELO
# ============================================

if page == "🔐 Gerar Selo":
    st.title("🔐 Gerar Selo Veraz")
    st.markdown("Crie uma impressão digital imutável, gere certificado visual e registre no GitHub.")

    col1, col2 = st.columns([3, 1])

    with col1:
        texto = st.text_area(
            "📝 Cole o conteúdo:",
            height=220,
            placeholder="Ex: Texto de notícia, artigo, declaração, contrato..."
        )

    with col2:
        tipo_conteudo = st.selectbox(
            "Tipo:",
            ["Texto", "Notícia", "Declaração", "Contrato", "Artigo", "Outro"]
        )
        autor = st.text_input("Autor:", placeholder="Nome ou organização")
        registrar_github = st.checkbox("Registrar no GitHub", value=True)

    if st.button("🔐 Gerar Selo", type="primary", use_container_width=True):
        if not texto.strip():
            st.warning("⚠️ Digite um conteúdo antes de gerar o selo.")
        else:
            st.session_state["selos_gerados"] += 1

            hash_conteudo = gerar_hash_conteudo(texto)
            metadados = gerar_metadados(texto, autor, tipo_conteudo, hash_conteudo)
            link_publico = gerar_link_verificacao(hash_conteudo)
            badge_html = gerar_badge_html(hash_conteudo)
            qr_bytes = gerar_qr_code_bytes(link_publico)
            certificado = gerar_certificado_publico(metadados, link_publico)

            st.markdown("""
            <div class="selo-card">
                <div class="selo-badge">✅ VERIFICADO</div>
                <h3>🏷️ Selo Veraz Gerado</h3>
                <div class="mini-muted">A verdade tem marca.</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("### 🔑 Hash SHA-256")
            st.code(hash_conteudo, language="text")

            st.markdown("### 🔗 Link completo de verificação")
            st.code(link_publico, language="text")

            col_qr, col_info = st.columns([1, 2])

            with col_qr:
                st.markdown("### 📱 QR Code")
                st.image(qr_bytes, caption="Escaneie para verificar", use_column_width=True)
                st.download_button(
                    "📥 Baixar QR Code",
                    data=qr_bytes,
                    file_name=f"qr-selo-veraz-{hash_conteudo[:12]}.png",
                    mime="image/png",
                    use_container_width=True
                )

            with col_info:
                st.markdown("### 📌 Compartilhamento")
                st.caption("Use o link ou o QR Code para validar o conteúdo publicamente.")

                st.markdown("### 🧩 Badge HTML")
                st.code(badge_html, language="html")

                st.download_button(
                    "📥 Baixar badge HTML",
                    data=badge_html,
                    file_name=f"badge-selo-veraz-{hash_conteudo[:12]}.html",
                    mime="text/html",
                    use_container_width=True
                )

            st.markdown("### 🏛️ Certificado visual")
            exibir_certificado_visual(metadados, link_publico)

            if registrar_github:
                if not github_token:
                    st.warning("⚠️ Configure o token GitHub na sidebar para registrar no repositório.")
                else:
                    with st.spinner("🔄 Registrando no GitHub..."):
                        g, user, erro = get_github_client(github_token)

                        if erro:
                            st.error(erro)
                        else:
                            repo, msg_repo = get_or_create_repo(user, github_repo_name)

                            if repo:
                                st.success(msg_repo)
                                resultado = commit_selo_github(repo, hash_conteudo, metadados)

                                if resultado["success"]:
                                    st.success("✅ Registrado no GitHub com sucesso!")

                                    if github_username:
                                        links_publicos = gerar_links_publicos(hash_conteudo, github_username, github_repo_name)
                                        with st.expander("🌐 Links públicos do selo"):
                                            st.code(links_publicos["blob_url"], language="text")
                                            st.code(links_publicos["raw_url"], language="text")

                                    col_a, col_b, col_c = st.columns(3)
                                    with col_a:
                                        st.link_button("🔗 Ver Commit", resultado["commit_url"], use_container_width=True)
                                    with col_b:
                                        st.link_button("📂 Ver Repo", resultado["repo_url"], use_container_width=True)
                                    with col_c:
                                        st.link_button("📄 Ver JSON", resultado["file_url"], use_container_width=True)
                                else:
                                    st.error(resultado["error"])
                            else:
                                st.error(msg_repo)

            with st.expander("📦 Metadados JSON"):
                st.json(metadados)

            with st.expander("📜 Certificado JSON"):
                st.json(certificado)

            json_str = json.dumps(metadados, indent=2, ensure_ascii=False)
            certificado_str = json.dumps(certificado, indent=2, ensure_ascii=False)

            col_d1, col_d2 = st.columns(2)
            with col_d1:
                st.download_button(
                    "📥 Baixar metadados JSON",
                    data=json_str,
                    file_name=f"selo-{hash_conteudo[:12]}.json",
                    mime="application/json",
                    use_container_width=True
                )
            with col_d2:
                st.download_button(
                    "📥 Baixar certificado JSON",
                    data=certificado_str,
                    file_name=f"certificado-selo-veraz-{hash_conteudo[:12]}.json",
                    mime="application/json",
                    use_container_width=True
                )

# ============================================
# PÁGINA 2 — VERIFICAR SELO
# ============================================

elif page == "🔍 Verificar Selo":
    st.title("🔍 Verificar Selo Veraz")
    st.markdown("Valide se um conteúdo é autêntico, registrado ou alterado.")

    if query_hash:
        st.markdown("""
        <div class="public-box">
            <strong>🔗 Verificação aberta por link público</strong><br>
            O hash foi carregado automaticamente pela URL.
        </div>
        """, unsafe_allow_html=True)

    metodo = st.radio(
        "Método de verificação:",
        ["🔑 Por Hash", "📝 Por Conteúdo", "🔗 Por URL do Commit"]
    )

    if metodo == "🔑 Por Hash":
        hash_input = st.text_input(
            "Hash SHA-256:",
            value=query_hash,
            placeholder="Cole aqui o hash completo"
        )

        modo_busca = st.radio(
            "Modo de busca:",
            ["🌐 Público", "🔐 Autenticado"],
            horizontal=True
        )

        if st.button("🔍 Buscar selo", type="primary"):
            if not hash_input.strip():
                st.warning("⚠️ Digite um hash para buscar.")
            else:
                st.session_state["verificacoes_feitas"] += 1
                hash_input = hash_input.strip()

                if modo_busca == "🌐 Público":
                    if not github_username:
                        st.error("❌ Defina o GITHUB_USERNAME nos secrets ou na sidebar.")
                    else:
                        with st.spinner("🌐 Consultando registro público..."):
                            resultado = buscar_selo_por_hash_publico(
                                hash_input,
                                github_username,
                                github_repo_name
                            )
                            exibir_resultado_verificacao_publica(resultado)

                            if resultado["encontrado"]:
                                link_publico = gerar_link_verificacao(hash_input)
                                qr_bytes = gerar_qr_code_bytes(link_publico)

                                st.markdown("### 🏛️ Certificado visual")
                                exibir_certificado_visual(resultado["metadados"], link_publico)

                                col1, col2 = st.columns(2)
                                with col1:
                                    st.image(qr_bytes, caption="QR do selo", use_column_width=True)
                                with col2:
                                    st.code(gerar_badge_html(hash_input), language="html")

                else:
                    if not github_token:
                        st.error("❌ Configure o token GitHub na sidebar.")
                    else:
                        with st.spinner("🔐 Buscando no GitHub autenticado..."):
                            g, user, erro = get_github_client(github_token)

                            if erro:
                                st.error(erro)
                            else:
                                repo, repo_error = get_repo(user, github_repo_name)

                                if repo:
                                    resultado = buscar_selo_por_hash_autenticado(repo, hash_input)

                                    if resultado["encontrado"]:
                                        st.markdown("""
                                        <div class="verification-box">
                                            <div class="status-verified">✅ CONTEÚDO VERIFICADO</div>
                                            <p>Este hash está registrado no Selo Veraz.</p>
                                        </div>
                                        """, unsafe_allow_html=True)

                                        st.markdown("### 📦 Metadados")
                                        st.json(resultado["metadados"])

                                        link_publico = gerar_link_verificacao(hash_input)
                                        qr_bytes = gerar_qr_code_bytes(link_publico)

                                        st.markdown("### 🏛️ Certificado visual")
                                        exibir_certificado_visual(resultado["metadados"], link_publico)

                                        col1, col2 = st.columns(2)
                                        with col1:
                                            if resultado.get("arquivo_url"):
                                                st.link_button("📄 Ver arquivo", resultado["arquivo_url"], use_container_width=True)
                                            st.image(qr_bytes, caption="QR do selo", use_column_width=True)
                                        with col2:
                                            if resultado.get("historico"):
                                                st.link_button("🔗 Último commit", resultado["historico"][0]["url"], use_container_width=True)
                                            st.code(gerar_badge_html(hash_input), language="html")

                                        if resultado.get("historico"):
                                            with st.expander("📜 Histórico"):
                                                for h in resultado["historico"]:
                                                    st.markdown(f"- **{h['data'][:10]}** — {h['mensagem']} [abrir]({h['url']})")
                                    else:
                                        st.markdown("""
                                        <div class="verification-box">
                                            <div class="status-notfound">⚠️ NÃO ENCONTRADO</div>
                                            <p>Este hash não está registrado no Selo Veraz.</p>
                                        </div>
                                        """, unsafe_allow_html=True)
                                else:
                                    st.error(f"❌ Não foi possível acessar o repositório: {repo_error}")

    elif metodo == "📝 Por Conteúdo":
        col1, col2 = st.columns(2)

        with col1:
            conteudo_atual = st.text_area(
                "Conteúdo para verificar:",
                height=220
            )

        with col2:
            hash_original = st.text_input(
                "Hash original:",
                placeholder="Cole o hash original"
            )

        if st.button("🔍 Verificar autenticidade", type="primary"):
            if not conteudo_atual.strip() or not hash_original.strip():
                st.warning("⚠️ Preencha o conteúdo e o hash original.")
            else:
                st.session_state["verificacoes_feitas"] += 1

                hash_atual = gerar_hash_conteudo(conteudo_atual)
                corresponde = hash_atual == hash_original.strip()

                if corresponde:
                    st.markdown("""
                    <div class="verification-box">
                        <div class="status-verified">✅ CONTEÚDO AUTÊNTICO</div>
                        <p>O conteúdo corresponde exatamente ao hash informado.</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="verification-box">
                        <div class="status-tampered">❌ CONTEÚDO ALTERADO</div>
                        <p>O conteúdo atual não corresponde ao hash original.</p>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown("### Comparação")
                    c1, c2 = st.columns(2)
                    with c1:
                        st.caption("Hash Original")
                        st.code(hash_original.strip(), language="text")
                    with c2:
                        st.caption("Hash Atual")
                        st.code(hash_atual, language="text")

    elif metodo == "🔗 Por URL do Commit":
        url_commit = st.text_input(
            "URL do Commit GitHub:",
            placeholder="https://github.com/usuario/repositorio/commit/..."
        )

        if st.button("🔍 Validar URL", type="primary"):
            if not url_commit.strip():
                st.warning("⚠️ Digite uma URL.")
            else:
                st.session_state["verificacoes_feitas"] += 1

                if "github.com" in url_commit and "/commit/" in url_commit:
                    st.success("✅ A URL parece ser um commit válido do GitHub.")
                    st.link_button("🌐 Abrir Commit", url_commit.strip(), use_container_width=True)
                else:
                    st.error("❌ URL inválida.")

# ============================================
# PÁGINA 3 — MEUS SELOS
# ============================================

elif page == "📊 Meus Selos":
    st.title("📊 Meus Selos Registrados")
    st.markdown("Visualize os registros armazenados no seu repositório GitHub.")

    if not github_token:
        st.warning("⚠️ Configure o token GitHub na sidebar para listar seus selos.")
    else:
        with st.spinner("🔄 Carregando seus selos..."):
            g, user, erro = get_github_client(github_token)

            if erro:
                st.error(erro)
            else:
                repo, repo_error = get_repo(user, github_repo_name)

                if repo:
                    try:
                        conteudos = repo.get_contents(SELOS_DIR)
                        arquivos_json = [c for c in conteudos if c.name.endswith(".json")]

                        if arquivos_json:
                            st.success(f"✅ {len(arquivos_json)} selo(s) encontrado(s)")

                            for item in arquivos_json[:50]:
                                try:
                                    conteudo_json = json.loads(item.decoded_content.decode("utf-8"))
                                    titulo = f"🏷️ {conteudo_json.get('tipo', 'Desconhecido')} — {conteudo_json.get('autor', 'Anônimo')}"
                                    with st.expander(titulo):
                                        st.json(conteudo_json)
                                        st.code(conteudo_json.get("hash", ""), language="text")

                                        hash_item = conteudo_json.get("hash", "")
                                        link_verificacao = gerar_link_verificacao(hash_item)

                                        col_a, col_b = st.columns(2)
                                        with col_a:
                                            st.code(link_verificacao, language="text")
                                        with col_b:
                                            st.code(gerar_badge_html(hash_item), language="html")

                                        if github_username:
                                            links_publicos = gerar_links_publicos(
                                                hash_item,
                                                github_username,
                                                github_repo_name
                                            )
                                            st.link_button(
                                                "🌐 Ver público",
                                                links_publicos["blob_url"],
                                                use_container_width=True
                                            )
                                        else:
                                            st.link_button(
                                                "🔗 Ver no GitHub",
                                                f"{repo.html_url}/blob/main/{item.path}",
                                                use_container_width=True
                                            )
                                except Exception:
                                    st.warning(f"⚠️ Erro ao ler {item.name}")
                        else:
                            st.info("📭 Nenhum selo registrado ainda.")
                    except Exception:
                        st.info("📭 A pasta de selos ainda não existe ou está vazia.")
                else:
                    st.error(f"❌ Não foi possível acessar o repositório: {repo_error}")

# ============================================
# FOOTER
# ============================================

st.markdown("---")
st.caption(f"🏷️ {APP_NAME} © 2026 • {APP_TAGLINE}")
