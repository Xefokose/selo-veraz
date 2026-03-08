import streamlit as st
import hashlib
import json
from datetime import datetime
from github import Github

# Configuração da página
st.set_page_config(
    page_title="Selo Veraz",
    page_icon="🏷️",
    layout="centered"
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
    .github-link {
        background: #24292e;
        color: white;
        padding: 8px 16px;
        border-radius: 8px;
        text-decoration: none;
        display: inline-block;
        margin: 10px 0;
    }
    .status-success { color: #00c853; font-weight: bold; }
    .status-error { color: #ff5252; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Header
st.title("🏷️ Selo Veraz")
st.subheader("A verdade tem marca.")
st.markdown("Gere e registre uma impressão digital imutável no GitHub.")

# --- Sidebar: Configurações ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/verified-account.png", width=80)
    st.markdown("### Sobre")
    st.markdown("""
    O **Selo Veraz** cria e registra um hash 
    criptográfico no GitHub, permitindo verificação 
    pública e imutável de qualquer conteúdo.
    """)
    
    st.markdown("---")
    st.markdown("### 🔑 Configuração GitHub")
    
    # Verificar se secrets estão configurados
    if hasattr(st.secrets, "GITHUB_TOKEN"):
        st.success("✅ Token GitHub configurado")
        github_token = st.secrets["GITHUB_TOKEN"]
        github_username = st.secrets.get("GITHUB_USERNAME", "")
    else:
        st.warning("⚠️ Configure o token em `.streamlit/secrets.toml`")
        github_token = st.text_input("Token GitHub:", type="password")
        github_username = st.text_input("Usuário GitHub:")
    
    st.markdown("---")
    st.markdown("### 📊 Estatísticas")
    st.metric("Selos Gerados (sessão)", st.session_state.get("selos_gerados", 0))

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
        
        # Tentar obter repo existente
        try:
            repo = user.get_repo(repo_name)
            return repo, False  # Repo já existia
        except:
            # Criar novo repo
            repo = user.create_repo(
                name=repo_name,
                description="🏷️ Registros imutáveis do Selo Veraz",
                private=False,  # Público para verificação
                auto_init=True
            )
            return repo, True  # Repo criado agora
    except Exception as e:
        return None, str(e)

def commit_selo_github(repo, hash_value: str, metadados: dict, conteudo: str):
    """Faz commit do selo no GitHub"""
    try:
        # Nome do arquivo baseado no hash (primeiros 12 caracteres)
        filename = f"selos/{hash_value[:12]}.json"
        
        # Conteúdo do arquivo JSON
        arquivo_conteudo = json.dumps(metadados, indent=2, ensure_ascii=False)
        
        # Verificar se arquivo já existe (para update)
        try:
            contents = repo.get_contents(filename)
            # Atualizar existente
            repo.update_file(
                path=filename,
                message=f"🏷️ Selo Veraz: {metadados['tipo']} - {metadados['autor']}",
                content=arquivo_conteudo,
                sha=contents.sha
            )
        except:
            # Criar novo
            repo.create_file(
                path=filename,
                message=f"🏷️ Novo Selo Veraz: {metadados['tipo']} - {metadados['autor']}",
                content=arquivo_conteudo
            )
        
        # Obter último commit
        commits = repo.get_commits()
        ultimo_commit = commits[0]
        
        return {
            "success": True,
            "commit_url": ultimo_commit.html_url,
            "repo_url": repo.html_url,
            "filename": filename
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# --- Área Principal ---

col1, col2 = st.columns([3, 1])

with col1:
    texto = st.text_area(
        "📝 Cole o conteúdo para gerar o Selo:",
        height=200,
        placeholder="Ex: Texto de notícia, artigo, declaração, contrato..."
    )

with col2:
    st.markdown("### Tipo de Conteúdo")
    tipo_conteudo = st.selectbox(
        "Selecione:",
        ["Texto", "Notícia", "Declaração", "Contrato", "Artigo", "Outro"],
        index=0
    )
    
    st.markdown("### Autor (Opcional)")
    autor = st.text_input("Nome:", placeholder="Seu nome ou organização")
    
    st.markdown("### Registrar no GitHub?")
    registrar_github = st.checkbox("Sim, criar commit público", value=True)

# --- Botão de Ação ---
if st.button("🔐 Gerar e Registrar Selo Veraz", type="primary", use_container_width=True):
    if texto:
        # Atualizar contador
        st.session_state["selos_gerados"] = st.session_state.get("selos_gerados", 0) + 1
        
        # Gerar hash e metadados
        hash_conteudo = gerar_hash_conteudo(texto)
        metadados = gerar_metadados(texto, autor, tipo_conteudo, hash_conteudo)
        
        # Exibir Card do Selo
        st.markdown("""
        <div class="selo-card">
            <div class="selo-badge">✅ VERIFICADO</div>
            <h3>🏷️ Selo Veraz Gerado</h3>
            <p>Impressão digital única criada com sucesso</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Exibir Hash
        st.markdown("### 🔑 Hash do Conteúdo (SHA-256)")
        st.code(hash_conteudo, language="text")
        
        # Botão para copiar hash
        st.copy_to_clipboard(hash_conteudo)
        st.success("✅ Hash copiado para a área de transferência!")
        
        # --- Integração GitHub ---
        if registrar_github and github_token:
            with st.spinner("🔄 Registrando no GitHub..."):
                # Criar/obter repo
                repo, repo_status = criar_repo_github(github_token, github_username)
                
                if repo:
                    if repo_status == True:
                        st.info(f"📂 Repositório criado: `{repo.name}`")
                    
                    # Fazer commit
                    resultado_commit = commit_selo_github(repo, hash_conteudo, metadados, texto)
                    
                    if resultado_commit["success"]:
                        st.success("✅ **Selo registrado no GitHub com sucesso!**")
                        
                        # Links
                        col_link1, col_link2 = st.columns(2)
                        with col_link1:
                            st.markdown(f"""
                            <a href="{resultado_commit['commit_url']}" target="_blank" class="github-link">
                                🔗 Ver Commit
                            </a>
                            """, unsafe_allow_html=True)
                        with col_link2:
                            st.markdown(f"""
                            <a href="{resultado_commit['repo_url']}" target="_blank" class="github-link">
                                📂 Ver Repositório
                            </a>
                            """, unsafe_allow_html=True)
                        
                        # Exibir metadados
                        with st.expander("📦 Ver Metadados Completos (JSON)"):
                            st.json(metadados)
                        
                        # Download
                        json_str = json.dumps(metadados, indent=2, ensure_ascii=False)
                        st.download_button(
                            label="📥 Baixar Metadados (.json)",
                            data=json_str,
                            file_name=f"selo-veraz-{hash_conteudo[:8]}.json",
                            mime="application/json"
                        )
                    else:
                        st.error(f"❌ Erro ao commitar: {resultado_commit['error']}")
                else:
                    st.error(f"❌ Erro ao acessar GitHub: {repo_status}")
        elif registrar_github and not github_token:
            st.warning("⚠️ Configure o token GitHub para registrar o selo.")
        
        # Preview do conteúdo (sempre exibir)
        with st.expander("📄 Preview do Conteúdo Original"):
            st.text(texto)
            
    else:
        st.warning("⚠️ Digite algum conteúdo para gerar o Selo.")

# --- Footer ---
st.markdown("---")
st.caption("🏷️ **Selo Veraz** © 2026 • Infraestrutura de confiança para a era digital")
st.caption("🔐 Hash SHA-256 • 📦 Metadados JSON • 🔗 GitHub Versioning")
