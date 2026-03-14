from flask import Flask, request, jsonify
from services.ai_engine import AIEngine
import os
from dotenv import load_dotenv

# 1. Carrega as variáveis do arquivo .env (chave do Gemini)
load_dotenv()

app = Flask(__name__)

# 2. Busca a chave que o Windows/Dotenv carregou
API_KEY = os.getenv("GEMINI_API_KEY")

# 3. Inicializa o motor de IA com a chave segura
if not API_KEY:
    print("❌ ERRO: GEMINI_API_KEY não encontrada no arquivo .env!")
    motor_ia = None
else:
    motor_ia = AIEngine(API_KEY)

def calcular_auditoria(milhas, taxas):
    """Regra: Cada 1.000 milhas custa R$ 10,00 + taxas."""
    return round((milhas / 1000 * 10.0) + taxas, 2)

def processar_json_latam(dados_json):
    """Extrai dados diretamente do formato técnico da LATAM (Custo 0)."""
    voos_extraidos = []
    itens = dados_json.get('content', [])
    
    for item in itens:
        summary = item.get('summary', {})
        if summary.get('brands'):
            # Seleciona a primeira tarifa disponível (index 0)
            tarifa = summary['brands'][0]
            milhas = tarifa.get('price', {}).get('amount', 0)
            taxas = tarifa.get('taxes', {}).get('amount', 0.0)
            
            voos_extraidos.append({
                "voo": summary.get('flightCode'),
                "origem": summary.get('origin', {}).get('iataCode'),
                "destino": summary.get('destination', {}).get('iataCode'),
                "data_hora": summary.get('origin', {}).get('departure'),
                "milhas": milhas,
                "taxas": taxas,
                "custo_total_estimado": calcular_auditoria(milhas, taxas)
            })
    return {"voos": voos_extraidos, "metodo": "parsing_direto_json"}

@app.route('/auditar', methods=['POST'])
def auditar():
    entrada = request.json
    
    # Caso 1: O usuário enviou o JSON técnico da LATAM (contém a chave 'content')
    if 'content' in entrada:
        try:
            resultado = processar_json_latam(entrada)
            return jsonify(resultado)
        except Exception as e:
            return jsonify({"erro": f"Falha ao processar JSON estruturado: {str(e)}"}), 500

    # Caso 2: O usuário enviou texto bruto para o Gemini
    texto_copiado = entrada.get('texto', '')
    if not texto_copiado:
        return jsonify({"erro": "Nenhum dado ou texto enviado para análise"}), 400

    if not motor_ia:
        return jsonify({"erro": "Motor de IA não configurado (chave ausente)"}), 500

    try:
        # Chama a IA para estruturar o texto
        resultado = motor_ia.extrair_dados_voo(texto_copiado)
        
        # Aplica a auditoria nos dados vindos da IA
        for voo in resultado.get('voos', []):
            milhas = voo.get('milhas', 0)
            taxas = voo.get('taxas', 0.0)
            voo['custo_total_estimado'] = calcular_auditoria(milhas, taxas)
        
        resultado['metodo'] = "ia_gemini"
        return jsonify(resultado)

    except Exception as e:
        return jsonify({"erro": f"Falha no processamento via IA: {str(e)}"}), 500

if __name__ == '__main__':
    print("🚀 Servidor MyMiles ativo!")
    print("💡 Pronto para processar JSON estruturado ou texto via Gemini.")
    app.run(host='0.0.0.0', port=5000, debug=True)