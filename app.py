import streamlit as st
import hashlib
import json
from datetime import datetime
from github import Github
import requests

# Configuração da página (atualizada)
st.set_page_config(
    page_title="Selo Veraz",
    page_icon="🏷️",
    layout="centered",  # Melhor para mobile
    initial_sidebar_state="collapsed",  # Sidebar fechada por padrão no mobile
    menu_items={
        "About": "Selo Veraz © 2026 - A verdade tem marca."
    }
)
# Configuração da página
st.set_page_config(
    page_title="Selo Veraz",
    page_icon="🏷️",
    layout="wide"
)

# CSS Personalizado
st.markdown("""
<style>
    .selo-card {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin: 2rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .selo-hash {
        font-family: 'Courier New', monospace;
        background: rgba(0,0,0,0.3);
        padding: 10px;
        border-radius: 8px;
        word-break: break-all;
        font-size: 0.85rem;
        margin: 10px 0;
    }
    .selo-badge {
        background: #00c853;
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
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
        font-size: 1.2rem;
    }
    .status-tampered { 
        background: #ff5252; 
        color: white; 
        padding: 10px 20px; 
        border-radius: 10px; 
        font-weight: bold;
        font-size: 1.2rem;
    }
    .status-notfound { 
        background: #ff9800; 
        color: white; 
        padding: 10px 20px; 
        border-radius: 10px; 
        font-weight: bold;
        font-size: 1.2rem;
    }
    .github-link {
        background: #24292e;
        color: white;
        padding: 8px 16px;
        border-radius: 8px;
        text-decoration: none;
        display: inline-block;
        margin: 10px 0;
    }
    .verification-box {
        background: #f5f5f5;
        padding: 20px;
        border-radius: 10px;
        margin: 20px 0;
        border-left: 5px solid #1e3a5f;
    }
</style>
""", unsafe_allow_html=True)

# --- Navegação entre Páginas ---
st.sidebar.markdown("### 🏷️ Selo Veraz")
page = st.sidebar.radio(
    "Navegação:",
    ["🔐 Gerar Selo", "🔍 Verificar Selo", "📊 Meus Selos"],
    index=0
)

# --- Sidebar: Configurações ---
with st.sidebar:
    st.markdown("---")
    st.markdown("### 🔑 Configuração GitHub")
    
    if hasattr(st.secrets, "GITHUB_TOKEN"):
        st.success("✅ Token configurado")
        github_token = st.secrets["GITHUB_TOKEN"]
        github_username = st.secrets.get("GITHUB_USERNAME", "")
    else:
        github_token = st.text_input("Token GitHub:", type="password", key="token_input")
        github_username = st.text_input("Usuário GitHub:", key="user_input")
    
    st.markdown("---")
    st.markdown("### 📊 Estatísticas")
    st.metric("Selos Gerados", st.session_state.get("selos_gerados", 0))
    st.metric("Verificações", st.session_state.get("verificacoes_feitas", 0))

# --- Funções ---

def gerar_hash_conteudo(conteudo: str) -> str:
    """Gera hash SHA-256 do conteúdo"""
    return hashlib.sha256(conteudo.encode('utf-8')).hexdigest()

def gerar_metadados(conteudo: str, autor: str, tipo: str, hash_value: str) -> dict:
    """Gera JSON com metadados do conteúdo"""
    return {
        "hash": hash_value,
        "autor": autor if autor else "Anônimo",
        "tipo": tipo,
        "data_criacao": datetime.now().isoformat(),
        "tamanho_bytes": len(conteudo.encode('utf-8')),
        "versao": "1.0.0",
        "plataforma": "Selo Veraz"
    }

def criar_repo_github(token: str, username: str, repo_name: str = "selo-veraz-registros"):
    """Cria ou obtém repositório no GitHub"""
    try:
        g = Github(token)
        user = g.get_user(username) if username else g.get_user()
        
        try:
            repo = user.get_repo(repo_name)
            return repo, False
        except:
            repo = user.create_repo(
                name=repo_name,
                description="🏷️ Registros imutáveis do Selo Veraz",
                private=False,
                auto_init=True
            )
            return repo, True
    except Exception as e:
        return None, str(e)

def commit_selo_github(repo, hash_value: str, metadados: dict, conteudo: str):
    """Faz commit do selo no GitHub"""
    try:
        filename = f"selos/{hash_value[:12]}.json"
        arquivo_conteudo = json.dumps(metadados, indent=2, ensure_ascii=False)
        
        try:
            contents = repo.get_contents(filename)
            repo.update_file(
                path=filename,
                message=f"🏷️ Selo Veraz: {metadados['tipo']} - {metadados['autor']}",
                content=arquivo_conteudo,
                sha=contents.sha
            )
        except:
            repo.create_file(
                path=filename,
                message=f"🏷️ Novo Selo Veraz: {metadados['tipo']} - {metadados['autor']}",
                content=arquivo_conteudo
            )
        
        commits = repo.get_commits()
        ultimo_commit = commits[0]
        
        return {
            "success": True,
            "commit_url": ultimo_commit.html_url,
            "repo_url": repo.html_url,
            "filename": filename
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def buscar_selo_por_hash(repo, hash_value: str) -> dict:
    """Busca selo no GitHub por hash"""
    try:
        filename = f"selos/{hash_value[:12]}.json"
        contents = repo.get_contents(filename)
        conteudo_json = json.loads(contents.decoded_content.decode('utf-8'))
        
        # Buscar histórico de commits deste arquivo
        commits = list(repo.get_commits(path=filename))
        historico = []
        for commit in commits[:10]:  # Últimos 10 commits
            historico.append({
                "data": commit.commit.author.date.isoformat(),
                "mensagem": commit.commit.message,
                "url": commit.html_url
            })
        
        return {
            "encontrado": True,
            "metadados": conteudo_json,
            "historico": historico
        }
    except:
        return {"encontrado": False}

def verificar_conteudo(conteudo: str, hash_original: str) -> bool:
    """Verifica se conteúdo corresponde ao hash"""
    hash_atual = gerar_hash_conteudo(conteudo)
    return hash_atual == hash_original

# ============================================
# PÁGINA 1: GERAR SELO
# ============================================
if page == "🔐 Gerar Selo":
    st.title("🔐 Gerar Selo Veraz")
    st.markdown("Crie uma impressão digital imutável e registre no GitHub.")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        texto = st.text_area(
            "📝 Cole o conteúdo:",
            height=200,
            placeholder="Ex: Texto de notícia, artigo, declaração..."
        )
    
    with col2:
        tipo_conteudo = st.selectbox(
            "Tipo:",
            ["Texto", "Notícia", "Declaração", "Contrato", "Artigo", "Outro"]
        )
        autor = st.text_input("Autor:", placeholder="Nome ou organização")
        registrar_github = st.checkbox("Registrar no GitHub", value=True)
    
    if st.button("🔐 Gerar Selo", type="primary", use_container_width=True):
        if texto:
            st.session_state["selos_gerados"] = st.session_state.get("selos_gerados", 0) + 1
            
            hash_conteudo = gerar_hash_conteudo(texto)
            metadados = gerar_metadados(texto, autor, tipo_conteudo, hash_conteudo)
            
            st.markdown("""
            <div class="selo-card">
                <div class="selo-badge">✅ VERIFICADO</div>
                <h3>🏷️ Selo Veraz Gerado</h3>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("### 🔑 Hash SHA-256")
            st.code(hash_conteudo, language="text")
            st.copy_to_clipboard(hash_conteudo)
            st.success("✅ Hash copiado!")
            
            if registrar_github and github_token:
                with st.spinner("🔄 Registrando no GitHub..."):
                    repo, _ = criar_repo_github(github_token, github_username)
                    if repo:
                        resultado = commit_selo_github(repo, hash_conteudo, metadados, texto)
                        if resultado["success"]:
                            st.success("✅ Registrado no GitHub!")
                            col_l1, col_l2 = st.columns(2)
                            with col_l1:
                                st.link_button("🔗 Ver Commit", resultado["commit_url"])
                            with col_l2:
                                st.link_button("📂 Ver Repo", resultado["repo_url"])
            
            with st.expander("📦 Metadados JSON"):
                st.json(metadados)
            
            json_str = json.dumps(metadados, indent=2, ensure_ascii=False)
            st.download_button(
                "📥 Baixar JSON",
                data=json_str,
                file_name=f"selo-{hash_conteudo[:8]}.json",
                mime="application/json"
            )
        else:
            st.warning("⚠️ Digite um conteúdo.")

# ============================================
# PÁGINA 2: VERIFICAR SELO
# ============================================
elif page == "🔍 Verificar Selo":
    st.title("🔍 Verificar Selo Veraz")
    st.markdown("Valide se um conteúdo é autêntico ou foi alterado.")
    
    metodo = st.radio(
        "Método de verificação:",
        ["🔑 Por Hash", "📝 Por Conteúdo", "🔗 Por URL do Commit"]
    )
    
    resultado_verificacao = None
    
    # --- Método 1: Por Hash ---
    if metodo == "🔑 Por Hash":
        hash_input = st.text_input(
            "Cole o hash SHA-256:",
            placeholder="Ex: a3f5b8c9d2e1f4a7b6c5d8e9f0a1b2c3..."
        )
        
        if st.button("🔍 Buscar", type="primary"):
            if hash_input and github_token:
                st.session_state["verificacoes_feitas"] = st.session_state.get("verificacoes_feitas", 0) + 1
                
                with st.spinner("🔍 Buscando no GitHub..."):
                    repo, _ = criar_repo_github(github_token, github_username)
                    if repo:
                        resultado = buscar_selo_por_hash(repo, hash_input)
                        
                        if resultado["encontrado"]:
                            st.markdown(f"""
                            <div class="verification-box">
                                <div class="status-verified">✅ CONTEÚDO VERIFICADO</div>
                                <p>Este hash está registrado no Selo Veraz</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.markdown("### 📦 Metadados")
                            st.json(resultado["metadados"])
                            
                            if resultado["historico"]:
                                with st.expander("📜 Histórico de Versões"):
                                    for h in resultado["historico"]:
                                        st.markdown(f"- **{h['data'][:10]}**: {h['mensagem']} [{link}]({h['url']})")
                        else:
                            st.markdown(f"""
                            <div class="verification-box">
                                <div class="status-notfound">⚠️ NÃO ENCONTRADO</div>
                                <p>Este hash não está registrado no Selo Veraz</p>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.error("Erro ao acessar GitHub")
            elif not github_token:
                st.warning("⚠️ Configure o token GitHub")
    
    # --- Método 2: Por Conteúdo ---
    elif metodo == "📝 Por Conteúdo":
        col_v1, col_v2 = st.columns(2)
        
        with col_v1:
            conteudo_atual = st.text_area(
                "Conteúdo para verificar:",
                height=200,
                key="conteudo_verificar"
            )
        
        with col_v2:
            hash_original = st.text_input(
                "Hash original:",
                placeholder="Cole o hash SHA-256 original"
            )
        
        if st.button("🔍 Verificar Autenticidade", type="primary"):
            if conteudo_atual and hash_original:
                st.session_state["verificacoes_feitas"] = st.session_state.get("verificacoes_feitas", 0) + 1
                
                hash_atual = gerar_hash_conteudo(conteudo_atual)
                corresponde = hash_atual == hash_original
                
                if corresponde:
                    st.markdown(f"""
                    <div class="verification-box">
                        <div class="status-verified">✅ CONTEÚDO AUTÊNTICO</div>
                        <p>O conteúdo não foi alterado desde a criação do selo</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="verification-box">
                        <div class="status-tampered">❌ CONTEÚDO ALTERADO</div>
                        <p>O conteúdo foi modificado! Hash não corresponde.</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("### Comparação de Hashes")
                    col_h1, col_h2 = st.columns(2)
                    with col_h1:
                        st.code(hash_original, language="text")
                        st.caption("Hash Original")
                    with col_h2:
                        st.code(hash_atual, language="text")
                        st.caption("Hash Atual")
            else:
                st.warning("⚠️ Preencha ambos os campos")
    
    # --- Método 3: Por URL ---
    elif metodo == "🔗 Por URL do Commit":
        url_commit = st.text_input(
            "URL do Commit GitHub:",
            placeholder="Ex: https://github.com/usuario/repo/commit/abc123..."
        )
        
        if st.button("🔍 Validar URL", type="primary"):
            if url_commit and github_token:
                st.session_state["verificacoes_feitas"] = st.session_state.get("verificacoes_feitas", 0) + 1
                
                try:
                    # Extrair info da URL
                    if "github.com" in url_commit and "/commit/" in url_commit:
                        st.success("✅ URL válida do GitHub")
                        st.info("🔗 Abra o link para ver os metadados do commit")
                        st.link_button("🌐 Abrir Commit", url_commit)
                    else:
                        st.error("❌ URL inválida")
                except:
                    st.error("❌ Erro ao validar URL")
            else:
                st.warning("⚠️ Preencha a URL")

# ============================================
# PÁGINA 3: MEUS SELOS
# ============================================
elif page == "📊 Meus Selos":
    st.title("📊 Meus Selos Registrados")
    st.markdown("Visualize todos os selos que você registrou.")
    
    if github_token and github_username:
        with st.spinner("🔄 Carregando seus selos..."):
            repo, _ = criar_repo_github(github_token, github_username)
            
            if repo:
                try:
                    # Buscar todos os arquivos na pasta selos/
                    conteudos = repo.get_contents("selos")
                    
                    if conteudos:
                        st.success(f"✅ {len(conteudos)} selos encontrados")
                        
                        for item in conteudos[:20]:  # Limitar a 20
                            try:
                                conteudo_json = json.loads(item.decoded_content.decode('utf-8'))
                                
                                with st.expander(f"🏷️ {conteudo_json.get('tipo', 'Desconhecido')} - {conteudo_json.get('autor', 'Anônimo')}"):
                                    st.json(conteudo_json)
                                    st.code(conteudo_json.get('hash', ''), language="text")
                                    st.link_button("🔗 Ver no GitHub", f"{repo.html_url}/blob/main/{item.path}")
                            except:
                                pass
                    else:
                        st.info("📭 Nenhum selo registrado ainda")
                except:
                    st.info("📭 Nenhum selo registrado ainda")
            else:
                st.warning("⚠️ Configure o token GitHub")
    else:
        st.warning("⚠️ Configure o token GitHub para ver seus selos")

# --- Footer ---
st.markdown("---")
st.caption("🏷️ **Selo Veraz** © 2026 • A verdade tem marca.")
