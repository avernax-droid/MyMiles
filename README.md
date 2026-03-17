# MyMiles ✈️ - Auditoria Inteligente de Passagens

O **MyMiles** é uma ferramenta de auditoria que utiliza Inteligência Artificial para comparar valores de voos em milhas e dinheiro, trazendo transparência para o mercado de fidelidade aérea.

## 🚀 Status do Projeto: Estabilização de IA Concluída
A aplicação opera com uma arquitetura de microsserviços containerizada, utilizando modelos de última geração para extração de dados.

## 📝 Histórico de Versões (Changelog)

### [2026-03-17] - Estabilização de IA e Melhoria Visual
- **Motor de IA:** Migração para o modelo `Gemini 1.5 Flash` (estável) para garantir consistência de cota e performance.
- **Inteligência de Interface:** Implementação de lógica automática de destaque (🥇 Verde) para a menor milhagem da lista.
- **Robustez de Dados:** Adicionado pré-processamento de texto no frontend para limpar "lixo" HTML antes do envio para a IA.
- **Diagnóstico:** Criação de ferramenta de validação de modelos disponíveis (`check_models.py`).

### [2026-03-14] - Fase 1: Interface e Docker
- **Interface Visual:** Criação do `index.html` com Bootstrap para exibição de tabelas.
- **Backend Robusto:** Configuração do servidor Flask rodando em Docker com Gunicorn.
- **Segurança:** Implementação de permissões CORS e variáveis de ambiente via `.env`.

## 🛠️ Tecnologias Utilizadas
- **IA:** Google Gemini SDK (`models/gemini-flash-latest`).
- **Backend:** Python 3.14, Flask, Gunicorn.
- **Frontend:** JavaScript (Vanilla), Bootstrap 5.
- **Infraestrutura:** Docker, WSL2, GitHub.

## ⚙️ Como Executar
1. Certifique-se de ter o arquivo `.env` com sua `GEMINI_API_KEY`.
2. Build da imagem: `docker build -t mymiles-app .`
3. Rodar o container: `docker run -p 5000:5000 --env-file .env mymiles-app`

---
*Desenvolvido como um projeto de automação e transparência em milhas aéreas.*