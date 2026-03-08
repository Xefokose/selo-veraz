import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Selo Veraz",
    page_icon="🏷️",
    layout="centered"
)

# Header
st.title("🏷️ Selo Veraz")
st.subheader("A verdade tem marca.")

# Input básico
texto = st.text_area("Cole o conteúdo para verificar:", height=150)

if st.button("Gerar Selo", type="primary"):
    if texto:
        st.success("✅ Conteúdo processado! (Em breve: hash + verificação)")
        st.code(texto[:100] + "..." if len(texto) > 100 else texto)
    else:
        st.warning("Digite algo para verificar.")

# Footer
st.markdown("---")
st.caption("Selo Veraz © 2026 • Infraestrutura de confiança para a era digital")
