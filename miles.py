import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

# Carrega variáveis de ambiente (Chave Gemini, etc)
load_dotenv()

app = Flask(__name__)
CORS(app)

# Caminho para salvar a sessão do navegador (Cookies) no Ubuntu
USER_DATA_DIR = os.path.join(os.getcwd(), ".auth")

def capturar_site_latam(origem, destino, data_ida, data_volta):
    """Acessa o site da LATAM usando a sessão persistente (cookies)."""
    with sync_playwright() as p:
        # Lança o navegador usando o perfil salvo na pasta .auth
        context = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,  # Mantenha False para você ver a automação agindo
            args=["--start-maximized"]
        )
        
        page = context.new_page()
        
        # URL de busca direta (Formato LATAM)
        url = f"https://www.latamairlines.com/br/pt/ofertas-voos?origin={origem}&outbound={data_ida}&destination={destino}&inbound={data_volta}&adt=1&typ=ROUND_TRIP&cabin=ECONOMY&redemption=true"
        
        try:
            print(f"Acessando: {url}")
            page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Espera um pouco para os voos carregarem na tela
            page.wait_for_timeout(10000) 
            
            # Captura o texto bruto da página para o Gemini processar
            conteudo = page.content()
            
            # Aqui você pode adicionar a lógica do seu parser.py depois
            context.close()
            return conteudo
            
        except Exception as e:
            print(f"Erro na captura: {e}")
            context.close()
            return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/buscar', methods=['POST'])
def buscar():
    dados = request.json
    # Exemplo de chamada: Latam (GRU -> MIA)
    resultado_bruto = capturar_site_latam(
        dados.get('origem', 'GRU'),
        dados.get('destino', 'MIA'),
        dados.get('data_ida', '2026-03-30'),
        dados.get('data_volta', '2026-04-06')
    )
    
    if resultado_bruto:
        return jsonify({"status": "sucesso", "mensagem": "Dados capturados com login persistente!"})
    else:
        return jsonify({"status": "erro", "mensagem": "Falha ao acessar o site."})

if __name__ == '__main__':
    # No WSL2, o host 0.0.0.0 permite que o Windows acesse o Flask
    app.run(debug=True, host='0.0.0.0', port=5000)
    