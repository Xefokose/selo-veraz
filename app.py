import streamlit as st
import hashlib
import json
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Selo Veraz",
    page_icon="🏷️",
    layout="centered"
)

# CSS Personalizado para o Card do Selo
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
        font-size: 0.9rem;
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
</style>
""", unsafe_allow_html=True)

# Header
st.title("🏷️ Selo Veraz")
st.subheader("A verdade tem marca.")
st.markdown("Gere uma impressão digital imutável para qualquer conteúdo digital.")

# --- Sidebar: Informações ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/verified-account.png", width=80)
    st.markdown("### Sobre")
    st.markdown("""
    O **Selo Veraz** cria um hash criptográfico único 
    para seu conteúdo, permitindo verificar se ele foi 
    alterado ao longo do tempo.
    
    **Tecnologia:** SHA-256 + Git Versioning
    """)
    st.markdown("---")
    st.markdown("### Status")
    st.success("🟢 Sistema Operacional")

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
        ["Texto", "Notícia", "Declaração", "Contrato", "Outro"],
        index=0
    )
    
    st.markdown("### Autor (Opcional)")
    autor = st.text_input("Nome:", placeholder="Seu nome ou organização")

# --- Função de Gerar Hash ---
def gerar_hash_conteudo(conteudo: str) -> str:
    """Gera hash SHA-256 do conteúdo"""
    return hashlib.sha256(conteudo.encode('utf-8')).hexdigest()

def gerar_metadados(conteudo: str, autor: str, tipo: str) -> dict:
    """Gera JSON com metadados do conteúdo"""
    return {
        "hash": gerar_hash_conteudo(conteudo),
        "autor": autor if autor else "Anônimo",
        "tipo": tipo,
        "data_criacao": datetime.now().isoformat(),
        "tamanho_bytes": len(conteudo.encode('utf-8')),
        "versao": "1.0.0"
    }

# --- Botão de Ação ---
if st.button("🔐 Gerar Selo Veraz", type="primary", use_container_width=True):
    if texto:
        # Gerar dados
        hash_conteudo = gerar_hash_conteudo(texto)
        metadados = gerar_metadados(texto, autor, tipo_conteudo)
        
        # Exibir Card do Selo
        st.markdown("""
        <div class="selo-card">
            <div class="selo-badge">✅ VERIFICADO</div>
            <h3>🏷️ Selo Veraz Gerado</h3>
            <p>Este conteúdo recebeu uma impressão digital única</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Exibir Hash
        st.markdown("### 🔑 Hash do Conteúdo (SHA-256)")
        st.code(hash_conteudo, language="text")
        
        # Botão para copiar hash
        st.copy_to_clipboard(hash_conteudo)
        st.success("✅ Hash copiado para a área de transferência!")
        
        # Exibir Metadados
        with st.expander("📦 Ver Metadados Completos (JSON)"):
            st.json(metadados)
        
        # Download do JSON
        json_str = json.dumps(metadados, indent=2, ensure_ascii=False)
        st.download_button(
            label="📥 Baixar Metadados (.json)",
            data=json_str,
            file_name=f"selo-veraz-{hash_conteudo[:8]}.json",
            mime="application/json"
        )
        
        # Preview do conteúdo
        with st.expander("📄 Preview do Conteúdo Original"):
            st.text(texto)
            
    else:
        st.warning("⚠️ Digite algum conteúdo para gerar o Selo.")

# --- Footer ---
st.markdown("---")
st.caption("🏷️ **Selo Veraz** © 2026 • Infraestrutura de confiança para a era digital")
st.caption("🔐 Hash SHA-256 • 📦 Metadados JSON • 🔗 Versionamento Git")
