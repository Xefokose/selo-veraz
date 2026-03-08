import streamlit as st
import hashlib
import json
from datetime import datetime
from github import Github, GithubException
import requests
import qrcode
from io import BytesIO
import pandas as pd

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
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={"About": f"{APP_NAME} © 2026 - {APP_TAGLINE}"}
)

# ============================================
# CSS
# ============================================

st.markdown("""
<style>
    .hero-box {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 55%, #2d5a87 100%);
        color: white;
        padding: 28px;
        border-radius: 20px;
        margin: 10px 0 24px 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.18);
    }
    .hero-title {
        font-size: 2rem;
        font-weight: 800;
        margin-bottom: 6px;
    }
    .hero-sub {
        opacity: 0.92;
        font-size: 1rem;
    }
    .metric-card {
        background: white;
        padding: 18px;
        border-radius: 16px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 4px 18px rgba(0,0,0,0.05);
        color: #111827;
    }
    .metric-title {
        font-size: 0.92rem;
        color: #6b7280;
        margin-bottom: 8px;
    }
    .metric-value {
        font-size: 1.75rem;
        font-weight: 800;
    }
    .metric-helper {
        margin-top: 6px;
        color: #4b5563;
        font-size: 0.9rem;
    }
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
    .history-box {
        background: #f8fafc;
        color: #111;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 14px;
        margin: 12px 0;
    }
    .timeline-step {
        background: #ffffff;
        border-left: 4px solid #1e3a5f;
        padding: 12px;
        margin: 10px 0;
        border-radius: 10px;
    }
    .summary-box {
        background: #ffffff;
        color: #111827;
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        padding: 18px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.04);
        margin: 12px 0;
    }
    .status-pill {
        display: inline-block;
        padding: 6px 12px;
        border-radius: 999px;
        font-weight: 700;
        font-size: 0.85rem;
    }
    .status-active {
        background: #dcfce7;
        color: #166534;
    }
    .status-archived {
        background: #f3f4f6;
        color: #374151;
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


def gerar_content_id(content_name: str, autor: str, tipo: str) -> str:
    base = f"{content_name.strip().lower()}|{autor.strip().lower()}|{tipo.strip().lower()}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:24]


def gerar_metadados(
    conteudo: str,
    autor: str,
    tipo: str,
    hash_value: str,
    content_name: str,
    content_id: str,
    version: int,
    previous_hash: str
) -> dict:
    agora = datetime.utcnow().isoformat() + "Z"
    return {
        "id": hash_value,
        "hash": hash_value,
        "content_id": content_id,
        "content_name": content_name.strip() if content_name.strip() else "Conteúdo sem nome",
        "version": version,
        "previous_hash": previous_hash.strip() if previous_hash.strip() else None,
        "autor": autor.strip() if autor.strip() else "Anônimo",
        "tipo": tipo,
        "data_criacao_utc": agora,
        "tamanho_bytes": len(conteudo.encode("utf-8")),
        "versao": "1.4.0",
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
    return {"raw_url": raw_url, "blob_url": blob_url}


def gerar_link_verificacao(hash_value: str):
    base = app_base_url.rstrip("/")
    return f"{base}/?hash={hash_value}"


def gerar_badge_html(hash_value: str):
    verify_url = gerar_link_verificacao(hash_value)
    return f'<a href="{verify_url}" target="_blank" rel="noopener noreferrer">✅ Verificado por Selo Veraz</a>'


def gerar_qr_code_bytes(texto: str):
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(texto)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.getvalue()


def gerar_certificado_publico(metadados: dict, link_verificacao: str):
    return {
        "selo_veraz": {
            "status": "verificado",
            "tagline": APP_TAGLINE,
            "id": metadados.get("id"),
            "hash": metadados.get("hash"),
            "content_id": metadados.get("content_id"),
            "content_name": metadados.get("content_name"),
            "version": metadados.get("version"),
            "previous_hash": metadados.get("previous_hash"),
            "autor": metadados.get("autor"),
            "tipo": metadados.get("tipo"),
            "data_criacao_utc": metadados.get("data_criacao_utc"),
            "tamanho_bytes": metadados.get("tamanho_bytes"),
            "versao": metadados.get("versao"),
            "plataforma": metadados.get("plataforma"),
            "link_verificacao": link_verificacao
        }
    }


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
                message=f"🏷️ Atualiza Selo Veraz v{metadados.get('version', 1)}: {metadados['tipo']} - {metadados['autor']}",
                content=arquivo_conteudo,
                sha=existing.sha
            )
        except GithubException:
            repo.create_file(
                path=filename,
                message=f"🏷️ Novo Selo Veraz v{metadados.get('version', 1)}: {metadados['tipo']} - {metadados['autor']}",
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
            return {
                "encontrado": True,
                "metadados": response.json(),
                "arquivo_url": links["blob_url"],
                "raw_url": links["raw_url"]
            }

        if response.status_code == 404:
            return {"encontrado": False, "mensagem": "Hash não encontrado no registro público"}

        return {
            "encontrado": False,
            "mensagem": f"Erro público ao consultar GitHub: HTTP {response.status_code}"
        }
    except Exception as e:
        return {"encontrado": False, "mensagem": f"Erro na verificação pública: {str(e)}"}


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
        <div class="cert-line"><strong>Nome do conteúdo:</strong> {metadados.get("content_name", "N/D")}</div>
        <div class="cert-line"><strong>Content ID:</strong> {metadados.get("content_id", "N/D")}</div>
        <div class="cert-line"><strong>Versão:</strong> {metadados.get("version", "N/D")}</div>
        <div class="cert-line"><strong>Hash anterior:</strong> {metadados.get("previous_hash", "Nenhum")}</div>
        <div class="cert-line"><strong>Autor:</strong> {metadados.get("autor", "Anônimo")}</div>
        <div class="cert-line"><strong>Tipo:</strong> {metadados.get("tipo", "N/D")}</div>
        <div class="cert-line"><strong>Data UTC:</strong> {metadados.get("data_criacao_utc", "N/D")}</div>
        <div class="cert-line"><strong>Tamanho:</strong> {metadados.get("tamanho_bytes", 0)} bytes</div>
        <div class="cert-line"><strong>Versão do sistema:</strong> {metadados.get("versao", "N/D")}</div>
        <div class="cert-line"><strong>Hash resumido:</strong> {hash_curto}</div>

        <div style="margin-top: 16px;"><strong>Link de verificação:</strong></div>
        <div class="hash-box">{link_verificacao}</div>

        <div style="margin-top: 16px;"><strong>Hash completo:</strong></div>
        <div class="hash-box">{hash_value}</div>
    </div>
    """, unsafe_allow_html=True)


def normalizar_data(data_str: str):
    try:
        return datetime.fromisoformat(data_str.replace("Z", "+00:00"))
    except Exception:
        return datetime.min


def carregar_todos_selos_repo(repo):
    dados = []
    try:
        conteudos = repo.get_contents(SELOS_DIR)
        arquivos_json = [c for c in conteudos if c.name.endswith(".json")]

        for item in arquivos_json:
            try:
                conteudo_json = json.loads(item.decoded_content.decode("utf-8"))
                conteudo_json["_path"] = item.path
                dados.append(conteudo_json)
            except Exception:
                continue
    except Exception:
        return []

    return dados


def agrupar_por_content_id(lista_selos):
    grupos = {}
    for selo in lista_selos:
        cid = selo.get("content_id", "sem-content-id")
        if cid not in grupos:
            grupos[cid] = []
        grupos[cid].append(selo)

    for cid in grupos:
        grupos[cid] = sorted(
            grupos[cid],
            key=lambda x: (x.get("version", 0), normalizar_data(x.get("data_criacao_utc", "")))
        )
    return grupos


def obter_proxima_versao_e_hash_anterior(lista_selos, content_id: str):
    relacionados = [s for s in lista_selos if s.get("content_id") == content_id]

    if not relacionados:
        return 1, ""

    relacionados_ordenados = sorted(
        relacionados,
        key=lambda x: (x.get("version", 0), normalizar_data(x.get("data_criacao_utc", "")))
    )
    ultimo = relacionados_ordenados[-1]
    return int(ultimo.get("version", 1)) + 1, ultimo.get("hash", "")


def filtrar_selos(lista_selos, busca_nome="", filtro_autor="", filtro_tipo=""):
    resultado = lista_selos

    if busca_nome.strip():
        termo = busca_nome.strip().lower()
        resultado = [s for s in resultado if termo in str(s.get("content_name", "")).lower()]

    if filtro_autor and filtro_autor != "Todos":
        resultado = [s for s in resultado if s.get("autor") == filtro_autor]

    if filtro_tipo and filtro_tipo != "Todos":
        resultado = [s for s in resultado if s.get("tipo") == filtro_tipo]

    return sorted(
        resultado,
        key=lambda x: normalizar_data(x.get("data_criacao_utc", "")),
        reverse=True
    )


def exibir_linha_historica(grupo):
    if not grupo:
        return

    st.markdown('<div class="history-box">', unsafe_allow_html=True)
    st.markdown(f"**Linha histórica:** {grupo[0].get('content_name', 'Sem nome')}")
    st.markdown(f"**Content ID:** `{grupo[0].get('content_id', 'N/D')}`")
    st.markdown(f"**Total de versões:** {len(grupo)}")

    for item in grupo:
        previous_hash = item.get("previous_hash") or "Nenhum"
        st.markdown(f"""
        <div class="timeline-step">
            <strong>Versão {item.get("version", "N/D")}</strong><br>
            <strong>Hash:</strong> <code>{item.get("hash", "")}</code><br>
            <strong>Hash anterior:</strong> <code>{previous_hash}</code><br>
            <strong>Autor:</strong> {item.get("autor", "Anônimo")}<br>
            <strong>Tipo:</strong> {item.get("tipo", "N/D")}<br>
            <strong>Data:</strong> {item.get("data_criacao_utc", "N/D")}
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


def montar_dataframe_selos(lista_selos):
    if not lista_selos:
        return pd.DataFrame()

    linhas = []
    for item in lista_selos:
        linhas.append({
            "content_name": item.get("content_name", ""),
            "content_id": item.get("content_id", ""),
            "version": item.get("version", 0),
            "hash": item.get("hash", ""),
            "previous_hash": item.get("previous_hash", ""),
            "autor": item.get("autor", ""),
            "tipo": item.get("tipo", ""),
            "data_criacao_utc": item.get("data_criacao_utc", ""),
            "tamanho_bytes": item.get("tamanho_bytes", 0),
            "versao_sistema": item.get("versao", ""),
            "plataforma": item.get("plataforma", ""),
            "link_verificacao": gerar_link_verificacao(item.get("hash", ""))
        })
    return pd.DataFrame(linhas)


def montar_resumo_dashboard(lista_selos):
    if not lista_selos:
        return {
            "total_selos": 0,
            "total_linhas": 0,
            "total_autores": 0,
            "total_tipos": 0,
            "media_versoes_por_linha": 0,
            "ultimo_registro": None,
            "maior_linha": None
        }

    grupos = agrupar_por_content_id(lista_selos)
    total_selos = len(lista_selos)
    total_linhas = len(grupos)
    total_autores = len(set([s.get("autor", "Anônimo") for s in lista_selos]))
    total_tipos = len(set([s.get("tipo", "Outro") for s in lista_selos]))
    media_versoes = round(total_selos / total_linhas, 2) if total_linhas else 0

    ultimo_registro = sorted(
        lista_selos,
        key=lambda x: normalizar_data(x.get("data_criacao_utc", "")),
        reverse=True
    )[0]

    maior_linha = sorted(
        grupos.items(),
        key=lambda x: len(x[1]),
        reverse=True
    )[0] if grupos else None

    return {
        "total_selos": total_selos,
        "total_linhas": total_linhas,
        "total_autores": total_autores,
        "total_tipos": total_tipos,
        "media_versoes_por_linha": media_versoes,
        "ultimo_registro": ultimo_registro,
        "maior_linha": maior_linha
    }


def contar_top_autores(lista_selos, limite=5):
    contagem = {}
    for item in lista_selos:
        autor = item.get("autor", "Anônimo")
        contagem[autor] = contagem.get(autor, 0) + 1
    return sorted(contagem.items(), key=lambda x: x[1], reverse=True)[:limite]


def contar_top_tipos(lista_selos, limite=5):
    contagem = {}
    for item in lista_selos:
        tipo = item.get("tipo", "Outro")
        contagem[tipo] = contagem.get(tipo, 0) + 1
    return sorted(contagem.items(), key=lambda x: x[1], reverse=True)[:limite]


def montar_linhas_consolidadas(lista_selos):
    grupos = agrupar_por_content_id(lista_selos)
    linhas = []

    for content_id, grupo in grupos.items():
        grupo_ordenado = sorted(grupo, key=lambda x: x.get("version", 0))
        mais_recente = grupo_ordenado[-1]
        linhas.append({
            "content_id": content_id,
            "content_name": mais_recente.get("content_name", "Sem nome"),
            "autor": mais_recente.get("autor", "Anônimo"),
            "tipo": mais_recente.get("tipo", "Outro"),
            "ultima_versao": mais_recente.get("version", 1),
            "hash_atual": mais_recente.get("hash", ""),
            "data_ultima_versao": mais_recente.get("data_criacao_utc", ""),
            "total_versoes": len(grupo_ordenado),
            "status": "Ativo"
        })

    return sorted(linhas, key=lambda x: normalizar_data(x["data_ultima_versao"]), reverse=True)


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
    ["🏠 Dashboard", "🔐 Gerar Selo", "🔍 Verificar Selo", "📊 Meus Selos"],
    index=2 if query_hash else 0
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
    st.markdown("### 📊 Sessão")
    st.metric("Selos Gerados", st.session_state["selos_gerados"])
    st.metric("Verificações", st.session_state["verificacoes_feitas"])

# ============================================
# CARREGAMENTO GLOBAL DO REPOSITÓRIO
# ============================================

repo_global = None
todos_selos_global = []
erro_repo_global = None

if github_token:
    g_global, user_global, erro_global = get_github_client(github_token)
    if not erro_global:
        repo_global, erro_repo_global = get_repo(user_global, github_repo_name)
        if repo_global:
            todos_selos_global = carregar_todos_selos_repo(repo_global)

# ============================================
# PÁGINA 1 — DASHBOARD
# ============================================

if page == "🏠 Dashboard":
    st.markdown(f"""
    <div class="hero-box">
        <div class="hero-title">🏷️ {APP_NAME}</div>
        <div class="hero-sub">{APP_TAGLINE}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("## Visão geral da plataforma")

    if not github_token:
        st.warning("⚠️ Configure o token GitHub na sidebar para carregar o dashboard.")
    elif erro_repo_global and not repo_global:
        st.error(f"❌ Não foi possível acessar o repositório: {erro_repo_global}")
    elif not todos_selos_global:
        st.info("📭 Nenhum selo encontrado ainda. Gere seus primeiros registros para alimentar o dashboard.")
    else:
        resumo = montar_resumo_dashboard(todos_selos_global)
        linhas_consolidadas = montar_linhas_consolidadas(todos_selos_global)
        df_selos = montar_dataframe_selos(todos_selos_global)

        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Total de Selos</div>
                <div class="metric-value">{resumo['total_selos']}</div>
                <div class="metric-helper">Registros imutáveis criados</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Linhas Históricas</div>
                <div class="metric-value">{resumo['total_linhas']}</div>
                <div class="metric-helper">Conteúdos acompanhados</div>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Autores</div>
                <div class="metric-value">{resumo['total_autores']}</div>
                <div class="metric-helper">Origens distintas</div>
            </div>
            """, unsafe_allow_html=True)
        with c4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Tipos</div>
                <div class="metric-value">{resumo['total_tipos']}</div>
                <div class="metric-helper">Categorias registradas</div>
            </div>
            """, unsafe_allow_html=True)
        with c5:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Média de Versões</div>
                <div class="metric-value">{resumo['media_versoes_por_linha']}</div>
                <div class="metric-helper">Evolução por conteúdo</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("## Resumo executivo")

        col_a, col_b = st.columns([2, 1])

        with col_a:
            ultimo = resumo["ultimo_registro"]
            if ultimo:
                st.markdown("""
                <div class="summary-box">
                """, unsafe_allow_html=True)
                st.markdown("### Último registro")
                st.write(f"**Conteúdo:** {ultimo.get('content_name', 'Sem nome')}")
                st.write(f"**Autor:** {ultimo.get('autor', 'Anônimo')}")
                st.write(f"**Tipo:** {ultimo.get('tipo', 'Outro')}")
                st.write(f"**Versão:** {ultimo.get('version', 1)}")
                st.write(f"**Data UTC:** {ultimo.get('data_criacao_utc', 'N/D')}")
                st.code(ultimo.get("hash", ""), language="text")
                st.markdown("</div>", unsafe_allow_html=True)

        with col_b:
            maior_linha = resumo["maior_linha"]
            if maior_linha:
                cid, grupo = maior_linha
                nome = grupo[-1].get("content_name", "Sem nome")
                st.markdown("""
                <div class="summary-box">
                """, unsafe_allow_html=True)
                st.markdown("### Linha histórica com mais versões")
                st.write(f"**Conteúdo:** {nome}")
                st.write(f"**Content ID:** `{cid}`")
                st.write(f"**Versões registradas:** {len(grupo)}")
                st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("## Distribuição operacional")

        col_top1, col_top2 = st.columns(2)

        with col_top1:
            st.markdown("### Top autores")
            top_autores = contar_top_autores(todos_selos_global, limite=10)
            if top_autores:
                for autor, qtd in top_autores:
                    st.write(f"**{autor}** — {qtd} selo(s)")
            else:
                st.info("Sem dados.")

        with col_top2:
            st.markdown("### Top tipos")
            top_tipos = contar_top_tipos(todos_selos_global, limite=10)
            if top_tipos:
                for tipo, qtd in top_tipos:
                    st.write(f"**{tipo}** — {qtd} selo(s)")
            else:
                st.info("Sem dados.")

        st.markdown("## Exportações")

        col_exp1, col_exp2 = st.columns(2)
        with col_exp1:
            csv_bytes = df_selos.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Exportar todos os selos em CSV",
                data=csv_bytes,
                file_name="selo-veraz-selos.csv",
                mime="text/csv",
                use_container_width=True
            )
        with col_exp2:
            json_bytes = json.dumps(todos_selos_global, indent=2, ensure_ascii=False).encode("utf-8")
            st.download_button(
                "📥 Exportar todos os selos em JSON",
                data=json_bytes,
                file_name="selo-veraz-selos.json",
                mime="application/json",
                use_container_width=True
            )

        st.markdown("## Últimos registros")
        ultimos = sorted(
            todos_selos_global,
            key=lambda x: normalizar_data(x.get("data_criacao_utc", "")),
            reverse=True
        )[:10]

        if ultimos:
            df_ultimos = pd.DataFrame([{
                "Conteúdo": x.get("content_name", ""),
                "Autor": x.get("autor", ""),
                "Tipo": x.get("tipo", ""),
                "Versão": x.get("version", 1),
                "Data UTC": x.get("data_criacao_utc", ""),
                "Hash": x.get("hash", "")
            } for x in ultimos])
            st.dataframe(df_ultimos, use_container_width=True)

        st.markdown("## Linhas históricas consolidadas")
        if linhas_consolidadas:
            df_linhas = pd.DataFrame(linhas_consolidadas)
            st.dataframe(df_linhas, use_container_width=True)

# ============================================
# PÁGINA 2 — GERAR SELO
# ============================================

elif page == "🔐 Gerar Selo":
    st.title("🔐 Gerar Selo Veraz")
    st.markdown("Crie uma impressão digital imutável com versionamento real.")

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

    st.markdown("### 🧬 Estrutura do conteúdo")
    modo_registro = st.radio(
        "Como deseja registrar?",
        ["🆕 Novo conteúdo", "🔁 Nova versão de conteúdo existente"],
        horizontal=True
    )

    content_name = st.text_input(
        "Nome do conteúdo:",
        placeholder="Ex: Nota oficial sobre resultado trimestral"
    )

    content_id_manual = ""
    previous_hash_manual = ""
    version_final = 1
    content_id_final = ""
    previous_hash_final = ""

    todos_selos = todos_selos_global if todos_selos_global else []

    if modo_registro == "🆕 Novo conteúdo":
        st.info("Você está criando uma nova linha histórica.")
        if content_name.strip():
            content_id_preview = gerar_content_id(content_name, autor, tipo_conteudo)
            st.code(content_id_preview, language="text")
            content_id_final = content_id_preview
        else:
            st.caption("Digite um nome de conteúdo para gerar o content_id.")

        version_final = 1
        previous_hash_final = ""

    else:
        st.info("Você está registrando uma nova versão de uma linha histórica já existente.")

        if todos_selos:
            opcoes = sorted(
                list({f"{s.get('content_name', 'Sem nome')} | {s.get('content_id', '')}" for s in todos_selos})
            )

            selecao = st.selectbox(
                "Selecione a linha histórica existente:",
                options=opcoes
            )

            if selecao:
                partes = selecao.split(" | ")
                nome_existente = partes[0].strip()
                cid_existente = partes[1].strip() if len(partes) > 1 else ""

                if not content_name.strip():
                    content_name = nome_existente

                content_id_final = cid_existente
                proxima_versao, hash_anterior = obter_proxima_versao_e_hash_anterior(todos_selos, cid_existente)
                version_final = proxima_versao
                previous_hash_final = hash_anterior

                st.markdown("### 📌 Dados da próxima versão")
                st.write(f"**Content ID:** `{content_id_final}`")
                st.write(f"**Próxima versão:** `{version_final}`")
                st.write(f"**Hash anterior:** `{previous_hash_final or 'Nenhum'}`")
        else:
            st.warning("⚠️ Nenhum conteúdo anterior encontrado. Cadastre primeiro um novo conteúdo.")
            content_id_manual = st.text_input("Content ID manual:", placeholder="Cole um content_id existente")
            previous_hash_manual = st.text_input("Hash anterior manual:", placeholder="Cole o hash da versão anterior")
            version_final = st.number_input("Versão", min_value=1, value=1, step=1)

            content_id_final = content_id_manual.strip()
            previous_hash_final = previous_hash_manual.strip()

    if st.button("🔐 Gerar Selo", type="primary", use_container_width=True):
        if not texto.strip():
            st.warning("⚠️ Digite um conteúdo antes de gerar o selo.")
        elif not content_name.strip():
            st.warning("⚠️ Informe o nome do conteúdo.")
        else:
            if modo_registro == "🆕 Novo conteúdo":
                content_id_final = gerar_content_id(content_name, autor, tipo_conteudo)
                version_final = 1
                previous_hash_final = ""
            else:
                if not content_id_final:
                    st.warning("⚠️ Não foi possível determinar o content_id da versão.")
                    st.stop()

            st.session_state["selos_gerados"] += 1

            hash_conteudo = gerar_hash_conteudo(texto)
            metadados = gerar_metadados(
                conteudo=texto,
                autor=autor,
                tipo=tipo_conteudo,
                hash_value=hash_conteudo,
                content_name=content_name,
                content_id=content_id_final,
                version=int(version_final),
                previous_hash=previous_hash_final
            )

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

            col_res1, col_res2 = st.columns(2)
            with col_res1:
                st.markdown("### 🔑 Hash SHA-256")
                st.code(hash_conteudo, language="text")
                st.markdown("### 🧬 Content ID")
                st.code(content_id_final, language="text")
            with col_res2:
                st.markdown("### 🔢 Versão")
                st.code(str(version_final), language="text")
                st.markdown("### ↩️ Hash anterior")
                st.code(previous_hash_final or "Nenhum", language="text")

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

            col_d1, col_d2 = st.columns(2)
            with col_d1:
                st.download_button(
                    "📥 Baixar metadados JSON",
                    data=json.dumps(metadados, indent=2, ensure_ascii=False),
                    file_name=f"selo-{hash_conteudo[:12]}.json",
                    mime="application/json",
                    use_container_width=True
                )
            with col_d2:
                st.download_button(
                    "📥 Baixar certificado JSON",
                    data=json.dumps(certificado, indent=2, ensure_ascii=False),
                    file_name=f"certificado-selo-veraz-{hash_conteudo[:12]}.json",
                    mime="application/json",
                    use_container_width=True
                )

# ============================================
# PÁGINA 3 — VERIFICAR SELO
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
                                            with st.expander("📜 Histórico de commits"):
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
            conteudo_atual = st.text_area("Conteúdo para verificar:", height=220)

        with col2:
            hash_original = st.text_input("Hash original:", placeholder="Cole o hash original")

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
# PÁGINA 4 — MEUS SELOS
# ============================================

elif page == "📊 Meus Selos":
    st.title("📊 Meus Selos Registrados")
    st.markdown("Visualize, filtre e acompanhe a evolução dos seus conteúdos.")

    if not github_token:
        st.warning("⚠️ Configure o token GitHub na sidebar para listar seus selos.")
    elif erro_repo_global and not repo_global:
        st.error(f"❌ Não foi possível acessar o repositório: {erro_repo_global}")
    else:
        todos_selos = todos_selos_global

        if not todos_selos:
            st.info("📭 Nenhum selo registrado ainda.")
        else:
            autores = sorted(list({s.get("autor", "Anônimo") for s in todos_selos}))
            tipos = sorted(list({s.get("tipo", "Outro") for s in todos_selos}))

            st.success(f"✅ {len(todos_selos)} selo(s) encontrado(s)")

            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                busca_nome = st.text_input("Buscar por nome do conteúdo:")
            with col_f2:
                filtro_autor = st.selectbox("Filtrar por autor:", ["Todos"] + autores)
            with col_f3:
                filtro_tipo = st.selectbox("Filtrar por tipo:", ["Todos"] + tipos)

            selos_filtrados = filtrar_selos(
                todos_selos,
                busca_nome=busca_nome,
                filtro_autor=filtro_autor,
                filtro_tipo=filtro_tipo
            )

            grupos = agrupar_por_content_id(selos_filtrados)
            linhas_consolidadas = montar_linhas_consolidadas(selos_filtrados)

            st.markdown("## Resumo filtrado")

            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Selos filtrados", len(selos_filtrados))
            with c2:
                st.metric("Linhas filtradas", len(grupos))
            with c3:
                media = round(len(selos_filtrados) / len(grupos), 2) if grupos else 0
                st.metric("Média de versões", media)

            if linhas_consolidadas:
                st.markdown("## Visão consolidada")
                df_linhas = pd.DataFrame(linhas_consolidadas)
                st.dataframe(df_linhas, use_container_width=True)

                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    st.download_button(
                        "📥 Exportar linhas filtradas em CSV",
                        data=df_linhas.to_csv(index=False).encode("utf-8"),
                        file_name="selo-veraz-linhas-filtradas.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                with col_e2:
                    st.download_button(
                        "📥 Exportar linhas filtradas em JSON",
                        data=json.dumps(linhas_consolidadas, indent=2, ensure_ascii=False).encode("utf-8"),
                        file_name="selo-veraz-linhas-filtradas.json",
                        mime="application/json",
                        use_container_width=True
                    )

            st.markdown("## Linhas históricas")

            for content_id, grupo in grupos.items():
                grupo_ordenado = sorted(grupo, key=lambda x: x.get("version", 0), reverse=True)
                mais_recente = grupo_ordenado[0]
                titulo = f"🏷️ {mais_recente.get('content_name', 'Sem nome')} — {mais_recente.get('autor', 'Anônimo')} — {len(grupo)} versão(ões)"

                with st.expander(titulo):
                    st.markdown(
                        '<span class="status-pill status-active">Versão mais recente ativa</span>',
                        unsafe_allow_html=True
                    )

                    exibir_linha_historica(sorted(grupo, key=lambda x: x.get("version", 0)))

                    st.markdown("### 📄 Versão mais recente")
                    st.json(mais_recente)

                    hash_item = mais_recente.get("hash", "")
                    link_verificacao = gerar_link_verificacao(hash_item)
                    qr_bytes = gerar_qr_code_bytes(link_verificacao)

                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.code(link_verificacao, language="text")
                        st.image(qr_bytes, caption="QR da versão atual", use_column_width=True)
                    with col_b:
                        st.code(gerar_badge_html(hash_item), language="html")
                        st.write(f"**Content ID:** `{mais_recente.get('content_id', '')}`")
                        st.write(f"**Última versão:** `{mais_recente.get('version', 1)}`")

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
                            f"{repo_global.html_url}/blob/main/{mais_recente.get('_path', '')}",
                            use_container_width=True
                        )

# ============================================
# FOOTER
# ============================================

st.markdown("---")
st.caption(f"🏷️ {APP_NAME} © 2026 • {APP_TAGLINE}")
