# MyMiles - Auditoria e Gestão de Milhas Aéreas

O **MyMiles** é uma aplicação web robusta desenvolvida em Python para auxiliar viajantes e estrategistas de milhas na gestão de suas aquisições e na busca de passagens. O sistema permite comparar o custo de voos em milhas versus dinheiro, 
calculando o **CPM (Custo por Milheiro)** em tempo real para garantir a melhor tomada de decisão.

## 🖥️ Ambiente de Desenvolvimento

O projeto utiliza um ecossistema moderno e híbrido, garantindo performance e isolamento de processos:

*   **Sistema Operacional:** Windows 11 Pro.
*   **Ambiente Linux:** **WSL2 (Windows Subsystem for Linux)** executando a distribuição **Ubuntu**.
*   **IDE:** **Visual Studio Code (VS Code)** com extensão *Remote - WSL*.
*   **Terminal:** Bash integrado no Ubuntu/VS Code.
*   **Containerização:** **Docker Desktop**, gerenciando o banco de dados MySQL (Porta 3307).
*   **Versionamento:** Git com repositório no **GitHub** (`avernax-droid`).

## 🚀 Funcionalidades Atuais

*   **Busca Inteligente (Sniper):** Interface para busca de voos integrando dados de aeroportos via JSON e lógica de busca automatizada.
*   **Gestão de Carteira:** Módulo de cadastro de aquisições (Programa, Quantidade, Valor Pago e Data).
*   **Cálculo de CPM:** Lógica automatizada para calcular o custo por cada mil milhas, tanto por transação individual quanto na média geral da carteira.
*   **Autenticação Segura:** Sistema de login e cadastro com criptografia de senhas (PBKDF2) e gestão de sessões.
*   **Exportação Excel-Ready:** Geração de relatórios em CSV com delimitador `;` e **BOM UTF-8**, configurado especificamente para abertura direta no Microsoft Excel sem erros de acentuação.

## 🛠️ Tecnologias Utilizadas

*   **Backend:** Python 3.x / Flask.
*   **Frontend:** HTML5, CSS3, Jinja2 Templates.
*   **Banco de Dados:** **MySQL** via Docker / SQLAlchemy (ORM).
*   **Segurança:** Flask-Login e Werkzeug Security.

## 📂 Estrutura de Arquivos (Versão Atual)

*   `server.py`: Núcleo da aplicação (Rotas, Auth, Banco e Exportação).
*   `engine.py`: Motor de busca e processamento de voos.
*   `aeroportos_sniper.json`: Base de dados local para suporte à busca.
*   `templates/`: Interfaces visuais (index, carteira, login, cadastro).

## 🔧 Como Instalar e Rodar

1. Certifique-se de que o container **MySQL** está ativo no Docker (Porta 3307).
2. Clone o repositório no seu ambiente Ubuntu/WSL2.
3. Instale as dependências:
   ```bash
   pip install flask flask-sqlalchemy flask-login mysql-connector-python