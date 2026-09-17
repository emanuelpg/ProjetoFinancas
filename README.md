# 💰 Finanças CV

Sistema de gerenciamento financeiro pessoal em Python com interface gráfica (Tkinter) e integração multimodal com a API Google Gemini para extração automática de comprovantes fiscais via QR Code/câmera do celular.

---

## 🚀 Funcionalidades

- **📸 Captura por QR Code:** Gera um QR Code local na rede Wi-Fi para capturar fotos de recibos diretamente pela câmera do celular.
- **🤖 Leitura com IA:** Utiliza o Google Gemini (`gemini-flash-lite-latest`) para extrair produtos e valores automaticamente das imagens.
- **✍️ Cadastro Manual e Flexível:** Formulários para lançamento rápido de despesas e receitas organizadas por categoria e método de pagamento.
- **📊 Painel de Análises:** Visualização em cartões e gráficos/tabelas para acompanhamento de despesas (Categorias, Fixos vs Não Fixos, Evolução Temporal, Métodos de Pagamento).
- **🗄️ Consulta SQL Direta:** Terminal integrado para execução de consultas SQLite personalizadas.

---

## 🛠️ Tecnologias Utilizadas

- **Linguagem:** Python 3.x
- **Interface Gráfica:** Tkinter / TTK
- **Banco de Dados:** SQLite3
- **Inteligência Artificial:** Google GenAI SDK (`google-genai`)
- **Processamento de Imagem & QR Code:** Pillow, qrcode

---

## 📋 Pré-requisitos

1. Python instalado na máquina.
2. Chave de API do Google Gemini ([Google AI Studio](https://aistudio.google.com/)).

---

## 🔧 Instalação e Configuração

1. **Clone o repositório:**
   ```bash
   git clone [https://github.com/seu-usuario/ProjetoFinancas.git](https://github.com/seu-usuario/ProjetoFinancas.git)
   cd ProjetoFinancas

2. Crie e ative o ambiente virtual (venv):
    * Windows:
        ```bash
        python -m venv venv
        .\venv\Scripts\activate
    
    * Linux/macOS:
        ```bash
        python3 -m venv venv
        source venv/bin/activate

3. **Instale as dependências:**
    ```bash
    pip install -r requirements.txt

4. **Configure as variáveis de ambiente:**
Crie um arquivo `.env` na raiz do projeto:
    ```Snippet de código
    GEMINI_API_KEY="SUA_CHAVE_AQUI"

---

## ▶️ Execução
Inicie a aplicação pelo terminal:

    python Main.py