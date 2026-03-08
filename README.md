# 🏷️ Selo Veraz

> **A verdade tem marca.**

O Selo Veraz é uma infraestrutura de confiança digital criada com **Streamlit + GitHub** para gerar, registrar e verificar impressões digitais imutáveis de conteúdos digitais usando **SHA-256**.

## 🚀 O que o sistema faz

- Gera hash SHA-256 de conteúdos
- Cria metadados estruturados em JSON
- Registra selos no GitHub
- Permite verificar autenticidade de conteúdos
- Mantém histórico público e rastreável

## 🧱 Tecnologias

- Python 3.10+
- Streamlit
- PyGithub
- GitHub API
- SHA-256

## 📦 Instalação local

```bash
git clone https://github.com/seu-usuario/selo-veraz.git
cd selo-veraz
pip install -r requirements.txt
streamlit run app.py
