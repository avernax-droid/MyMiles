import os
import logging
import sys
import asyncio
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from playwright.async_api import async_playwright

# Importa o motor de IA
from services.ai_engine import AIEngine

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(message)s', 
    handlers=[logging.StreamHandler(sys.stdout)]
)
load_dotenv()

app = Flask(__name__, template_folder='.', static_folder='.')
CORS(app)

# Inicializa o Gemini
ai_brain = AIEngine(os.getenv("GEMINI_API_KEY"))

# Configuração de Caminhos no Linux
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUTH_DIR = os.path.join(BASE_DIR, ".auth", "latam_session")

async def capturar_site_latam(origem, destino, data):
    url = f"https://www.latamairlines.com/br/pt/oferta-voos?origin={origem}&destination={destino}&departure={data}&adult=1&cabin=economy&redemption=true"
    
    async with async_playwright() as p:
        logging.info(f"🕵️ Abrindo navegador no Ubuntu (WSL): {origem} -> {destino}")
        
        # --- MUDANÇA AQUI: USANDO CONTEXTO PERSISTENTE ---
        context = await p.chromium.launch_persistent_context(
            user_data_dir=AUTH_DIR, # Aqui moram os cookies
            headless=False, 
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            args=['--disable-blink-features=AutomationControlled']
        )
        
        # No launch_persistent_context, a página já vem aberta
        page = context.pages[0] if context.pages else await context.new_page()
        await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        try:
            logging.info("🔗 Navegando para a página de busca...")
            await page.goto(url, wait_until="networkidle", timeout=90000)
            
            # --- INTERVENÇÃO ---
            # Se for a PRIMEIRA vez, você terá 60 segundos para logar se o site pedir.
            # Nas próximas, esse tempo serve para o site carregar os preços.
            logging.info("⏳ Aguardando carregamento (Aproveite para logar se necessário)...")
            await asyncio.sleep(40) 
            
            logging.info("📜 Forçando carregamento de elementos via Scroll...")
            await page.mouse.wheel(0, 1500) 
            await asyncio.sleep(3)
            
            # Captura o conteúdo
            conteudo = await page.evaluate("() => document.body.innerText")
            logging.info(f"📊 Texto capturado: {len(conteudo)} caracteres.")
            
            await context.close()
            return conteudo
            
        except Exception as e:
            logging.error(f"❌ Erro no Playwright: {e}")
            if 'context' in locals(): await context.close()
            return None

# ... (Mantenha as rotas @app.route iguaizinhas ao seu código original) ...

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/buscar', methods=['POST'])
def buscar():
    try:
        dados = request.json
        origem = dados.get('origem', '').upper()
        destino = dados.get('destino', '').upper()
        data_ida = dados.get('data_ida')

        if not all([origem, destino, data_ida]):
            return jsonify({"voos": [], "erro": "Preencha todos os campos."}), 400

        # Captura assíncrona
        texto_site = asyncio.run(capturar_site_latam(origem, destino, data_ida))

        if texto_site and len(texto_site) > 1500:
            logging.info("🧠 Enviando para o Gemini processar os dados...")
            resultado = ai_brain.extrair_dados_voo(texto_site)
            if resultado.get("voos"):
                return jsonify(resultado)
            else:
                return jsonify({"voos": [], "erro": "IA não encontrou voos no texto capturado."}), 404
        
        return jsonify({
            "voos": [], 
            "erro": f"Conteúdo insuficiente para análise ({len(texto_site) if texto_site else 0} chars)."
        }), 502

    except Exception as e:
        logging.error(f"❌ Erro Geral: {e}")
        return jsonify({"voos": [], "erro": "Erro interno no servidor MyMiles."}), 500

if __name__ == '__main__':
    # Rodando no host local do Windows via WSL
    app.run(host='127.0.0.1', port=5000, debug=False)