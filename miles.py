from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS 
from services.ai_engine import AIEngine
import os
from dotenv import load_dotenv

# 1. Carrega as variáveis do arquivo .env
load_dotenv()

# AJUSTE: Informamos ao Flask que a pasta de templates é a raiz atual ('.')
app = Flask(__name__, template_folder='.', static_folder='.')
CORS(app)

# 2. Busca a chave do Gemini
API_KEY = os.getenv("GEMINI_API_KEY")

# 3. Inicializa o motor de IA
if not API_KEY:
    print("❌ ERRO: GEMINI_API_KEY não encontrada no arquivo .env!")
    motor_ia = None
else:
    motor_ia = AIEngine(API_KEY)

def calcular_auditoria(milhas, taxas):
    """Regra: Cada 1.000 milhas custa R$ 10,00 + taxas."""
    try:
        m = float(milhas)
        t = float(taxas)
        return round((m / 1000 * 10.0) + t, 2)
    except:
        return 0.0

# --- NOVA ROTA: Serve o index.html da raiz ---
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

def processar_json_latam(dados_json):
    """Extrai dados diretamente do formato técnico da LATAM (F12)."""
    voos_extraidos = []
    itens = dados_json.get('content', [])
    
    for item in itens:
        summary = item.get('summary', {})
        if summary.get('brands'):
            tarifa = summary['brands'][0]
            milhas = tarifa.get('price', {}).get('amount', 0)
            taxas = tarifa.get('taxes', {}).get('amount', 0.0)
            
            voos_extraidos.append({
                "voo": summary.get('flightCode'),
                "cia": "LATAM", # Fixo para o JSON técnico da Latam
                "trecho": f"{summary.get('origin', {}).get('iataCode')} ➔ {summary.get('destination', {}).get('iataCode')}",
                "milhas": milhas,
                "taxas": taxas,
                "custo_total_estimado": calcular_auditoria(milhas, taxas)
            })
    return {"voos": voos_extraidos, "metodo": "parsing_direto_json"}

@app.route('/auditar', methods=['POST'])
def auditar():
    entrada = request.json
    
    # Caso 1: JSON técnico da LATAM
    if 'content' in entrada:
        try:
            resultado = processar_json_latam(entrada)
            return jsonify(resultado)
        except Exception as e:
            return jsonify({"erro": f"Falha ao processar JSON estruturado: {str(e)}"}), 500

    # Caso 2: Texto bruto para o Gemini
    texto_copiado = entrada.get('texto', '')
    if not texto_copiado:
        return jsonify({"erro": "Nenhum dado ou texto enviado para análise"}), 400

    if not motor_ia:
        return jsonify({"erro": "Motor de IA não configurado (chave ausente)"}), 500

    try:
        # Chama a IA para estruturar o texto
        resultado = motor_ia.extrair_dados_voo(texto_copiado)
        
        # Aplica a auditoria nos dados vindos da IA
        if "voos" in resultado:
            for voo in resultado.get('voos', []):
                milhas = voo.get('milhas', 0)
                taxas = voo.get('taxas', 0.0)
                voo['custo_total_estimado'] = calcular_auditoria(milhas, taxas)
        
        resultado['metodo'] = "ia_gemini"
        return jsonify(resultado)

    except Exception as e:
        return jsonify({"erro": f"Falha no processamento via IA: {str(e)}"}), 500

if __name__ == '__main__':
    print("🚀 Servidor MyMiles ativo em http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)