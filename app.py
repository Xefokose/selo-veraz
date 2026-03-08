import streamlit as st
import hashlib
import json
from datetime import datetime
from github import Github, GithubException

# Configuração da página
st.set_page_config(
    page_title="Selo Veraz",
    page_icon="🏷️",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items={
        "About": "Selo Veraz © 2026 - A verdade tem marca."
    }
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
    .verification-box {
        background: #f5f5f5;
        padding: 20px;
        border-radius: 10px;
        margin: 20px 0;
        border-left: 5px solid #1e3a5f;
    }
    .error-box {
        background: #ffebee;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #ff5252;
        margin: 10px 0;
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

def get_github_repo(token: str, username: str, repo_name: str = "selo-veraz-registros"):
    """Obtém ou cria repositório no GitHub com tratamento de erro robusto"""
    try:
        g = Github(token)
        
        # Verifica se o token é válido
        try:
            user = g.get_user(username) if username else g.get_user()
            user.login  # Testa se o usuário é válido
        except GithubException as e:
            return None, f"❌ Token inválido ou expirado. Erro: {str(e)}"
        
        # Tenta obter o repositório existente
        try:
            repo = user.get_repo(repo_name)
            return repo, None  # Sucesso, repo existe
        except GithubException:
            # Repo não existe, cria um novo
            try:
                repo = user.create_repo(
                    name=repo_name,
                    description="🏷️ Registros imutáveis do Selo Veraz",
                    private=False,
                    auto_init=True
                )
                return repo, None  # Sucesso, repo criado
            except GithubException as e:
                return None, f"❌ Erro ao criar repositório: {str(e)}"
                
    except Exception as e:
        return None, f"❌ Erro de conexão com GitHub: {str(e)}"

def garantir_pasta_selos(repo):
    """Garante que a pasta selos/ exista no repositório"""
    try:
        # Tenta acessar a pasta selos
        repo.get_contents("selos")
        return True, None
    except:
        # Pasta não existe, cria um arquivo .gitignore para criar a pasta
        try:
            repo.create_file(
                path="selos/.gitkeep",
                message="📁 Cria pasta selos/",
                content="# Esta pasta armazena os selos veraz\n"
            )
            return True, None
        except Exception as e:
            return False, f"Erro ao criar pasta selos: {str(e)}"

def commit_selo_github(repo, hash_value: str, metadados: dict):
    """Faz commit do selo no GitHub com tratamento de erro"""
    try:
        # Garante que a pasta existe
        sucesso, erro = garantir_pasta_selos(repo)
        if not sucesso:
            return {"success": False, "error": erro}
        
        filename = f"selos/{hash_value[:12]}.json"
        arquivo_conteudo = json.dumps(metadados, indent=2, ensure_ascii=False)
        
        # Verifica se arquivo já existe
        try:
            contents = repo.get_contents(filename)
            # Atualiza existente
            repo.update_file(
                path=filename,
                message=f"🏷️ Selo Veraz: {metadados['tipo']} - {metadados['autor']}",
                content=arquivo_conteudo,
                sha=contents.sha
            )
        except GithubException:
            # Cria novo arquivo
            repo.create_file(
                path=filename,
                message=f"🏷️ Novo Selo Veraz: {metadados['tipo']} - {metadados['autor']}",
                content=arquivo_conteudo
            )
        
        # Obtém URL do último commit
        commits = repo.get_commits()
        ultimo_commit = commits[0]
        
        return {
            "success": True,
            "commit_url": ultimo_commit.html_url,
            "repo_url": repo.html_url,
            "filename": filename
        }
    except Exception as e:
        return {"success": False, "error": f"Erro ao fazer commit: {str(e)}"}

def buscar_selo_por_hash(repo, hash_value: str):
    """Busca selo no GitHub por hash com tratamento de erro detalhado"""
    try:
        filename = f"selos/{hash_value[:12]}.json"
        
        # Tenta obter o arquivo
        try:
            contents = repo.get_contents(filename)
            conteudo_json = json.loads(contents.decoded_content.decode('utf-8'))
            
            # Busca histórico de commits
            try:
                commits = list(repo.get_commits(path=filename))
                historico = []
                for commit in commits[:10]:
                    historico.append({
                        "data": commit.commit.author.date.isoformat(),
                        "mensagem": commit.commit.message,
                        "url": commit.html_url
                    })
            except:
                historico = []
            
            return {
                "encontrado": True,
                "metadados": conteudo_json,
                "historico": historico
            }
        except GithubException:
            # Arquivo não encontrado
            return {"encontrado": False, "mensagem": "Hash não registrado no sistema"}
            
    except Exception as e:
        return {"encontrado": False, "mensagem": f"Erro na busca: {str(e)}"}

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
            st.caption("💡 Clique no ícone 📋 no canto direito para copiar")
            
            if registrar_github and github_token:
                with st.spinner("🔄 Registrando no GitHub..."):
                    repo, erro = get_github_repo(github_token, github_username)
                    
                    if erro:
                        st.error(erro)
                    elif repo:
                        resultado = commit_selo_github(repo, hash_conteudo, metadados)
                        
                        if resultado["success"]:
                            st.success("✅ Registrado no GitHub com sucesso!")
                            col_l1, col_l2 = st.columns(2)
                            with col_l1:
                                st.link_button("🔗 Ver Commit", resultado["commit_url"])
                            with col_l2:
                                st.link_button("📂 Ver Repo", resultado["repo_url"])
                        else:
                            st.error(f"❌ {resultado['error']}")
            elif registrar_github and not github_token:
                st.warning("⚠️ Configure o token GitHub na sidebar para registrar")
            
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
    
    if not github_token:
        st.warning("⚠️ Configure o token GitHub na sidebar para usar a verificação")
    
    metodo = st.radio(
        "Método de verificação:",
        ["🔑 Por Hash", "📝 Por Conteúdo", "🔗 Por URL do Commit"]
    )
    
    # --- Método 1: Por Hash ---
    if metodo == "🔑 Por Hash":
        st.markdown("### 🔑 Verificar por Hash")
        st.markdown("Cole o hash SHA-256 para buscar no registro:")
        
        hash_input = st.text_input(
            "Hash SHA-256:",
            placeholder="Ex: 2672fb6e0b91928df7f781df03917ee636066e2c18efcba7dd611505075d2d2a"
        )
        
        if st.button("🔍 Buscar no GitHub", type="primary"):
            if not hash_input:
                st.warning("⚠️ Digite um hash para buscar")
            elif not github_token:
                st.error("❌ Configure o token GitHub na sidebar")
            else:
                st.session_state["verificacoes_feitas"] = st.session_state.get("verificacoes_feitas", 0) + 1
                
                with st.spinner("🔍 Buscando no GitHub..."):
                    repo, erro = get_github_repo(github_token, github_username)
                    
                    if erro:
                        st.error(erro)
                    elif repo:
                        resultado = buscar_selo_por_hash(repo, hash_input)
                        
                        if resultado["encontrado"]:
                            st.markdown("""
                            <div class="verification-box">
                                <div class="status-verified">✅ CONTEÚDO VERIFICADO</div>
                                <p>Este hash está registrado no Selo Veraz</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.markdown("### 📦 Metadados")
                            st.json(resultado["metadados"])
                            
                            if resultado.get("historico"):
                                with st.expander("📜 Histórico de Versões"):
                                    for h in resultado["historico"]:
                                        st.markdown(f"- **{h['data'][:10]}**: {h['mensagem']} [🔗]({h['url']})")
                        else:
                            st.markdown("""
                            <div class="verification-box">
                                <div class="status-notfound">⚠️ NÃO ENCONTRADO</div>
                                <p>Este hash não está registrado no Selo Veraz</p>
                            </div>
                            """, unsafe_allow_html=True)
                            st.info(f"💡 Mensagem: {resultado.get('mensagem', 'Desconhecido')}")
    
    # --- Método 2: Por Conteúdo ---
    elif metodo == "📝 Por Conteúdo":
        st.markdown("### 📝 Verificar por Conteúdo")
        st.markdown("Compare o conteúdo atual com o hash original:")
        
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
            if not conteudo_atual or not hash_original:
                st.warning("⚠️ Preencha ambos os campos")
            else:
                st.session_state["verificacoes_feitas"] = st.session_state.get("verificacoes_feitas", 0) + 1
                
                hash_atual = gerar_hash_conteudo(conteudo_atual)
                corresponde = hash_atual == hash_original
                
                if corresponde:
                    st.markdown("""
                    <div class="verification-box">
                        <div class="status-verified">✅ CONTEÚDO AUTÊNTICO</div>
                        <p>O conteúdo não foi alterado desde a criação do selo</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
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
    
    # --- Método 3: Por URL ---
    elif metodo == "🔗 Por URL do Commit":
        st.markdown("### 🔗 Verificar por URL do Commit")
        
        url_commit = st.text_input(
            "URL do Commit GitHub:",
            placeholder="Ex: https://github.com/usuario/selo-veraz-registros/commit/abc123..."
        )
        
        if st.button("🔍 Validar URL", type="primary"):
            if not url_commit:
                st.warning("⚠️ Digite uma URL")
            else:
                st.session_state["verificacoes_feitas"] = st.session_state.get("verificacoes_feitas", 0) + 1
                
                if "github.com" in url_commit and "/commit/" in url_commit:
                    st.success("✅ URL válida do GitHub")
                    st.info("🔗 Clique abaixo para abrir o commit e ver os metadados")
                    st.link_button("🌐 Abrir Commit", url_commit)
                else:
                    st.error("❌ URL inválida. Deve ser uma URL de commit do GitHub")

# ============================================
# PÁGINA 3: MEUS SELOS
# ============================================
elif page == "📊 Meus Selos":
    st.title("📊 Meus Selos Registrados")
    st.markdown("Visualize todos os selos que você registrou.")
    
    if not github_token or not github_username:
        st.warning("⚠️ Configure o token e usuário GitHub na sidebar para ver seus selos")
    else:
        with st.spinner("🔄 Carregando seus selos..."):
            repo, erro = get_github_repo(github_token, github_username)
            
            if erro:
                st.error(erro)
            elif repo:
                try:
                    # Tenta acessar a pasta selos
                    try:
                        conteudos = repo.get_contents("selos")
                        
                        # Filtra apenas arquivos JSON (ignora .gitkeep)
                        arquivos_json = [c for c in conteudos if c.name.endswith('.json')]
                        
                        if arquivos_json:
                            st.success(f"✅ {len(arquivos_json)} selos encontrados")
                            
                            # Mostra os 20 mais recentes
                            for item in arquivos_json[:20]:
                                try:
                                    conteudo_json = json.loads(item.decoded_content.decode('utf-8'))
                                    
                                    with st.expander(f"🏷️ {conteudo_json.get('tipo', 'Desconhecido')} - {conteudo_json.get('autor', 'Anônimo')}"):
                                        st.json(conteudo_json)
                                        st.code(conteudo_json.get('hash', ''), language="text")
                                        st.link_button("🔗 Ver no GitHub", f"{repo.html_url}/blob/main/{item.path}")
                                except Exception as e:
                                    st.warning(f"⚠️ Erro ao ler arquivo {item.name}: {str(e)}")
                        else:
                            st.info("📭 Nenhum selo registrado ainda. Gere seu primeiro selo na página 'Gerar Selo'!")
                    except GithubException:
                        st.info("📭 A pasta 'selos' não existe ainda. Gere seu primeiro selo para criá-la!")
                except Exception as e:
                    st.error(f"❌ Erro ao carregar selos: {str(e)}")
                    st.exception(e)  # Mostra detalhes do erro para debug

# --- Footer ---
st.markdown("---")
st.caption("🏷️ **Selo Veraz** © 2026 • A verdade tem marca.")
