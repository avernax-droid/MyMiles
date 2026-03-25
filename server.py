from flask import Flask, render_template, request, jsonify
import os
from engine import buscar_voos_completos

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/buscar', methods=['POST'])
def buscar():
    try:
        params = request.get_json()
        origem = params.get('origem', '').upper().strip()
        destino = params.get('destino', '').upper().strip()
        data_ida = params.get('data_ida')
        data_volta = params.get('data_volta')
        
        print(f"\n🚀 MyMiles Sniper iniciando busca: {origem} -> {destino}")
        
        dados_voos = buscar_voos_completos(origem, destino, data_ida, data_volta)
        
        if dados_voos:
            return jsonify({"status": "sucesso", "dados": dados_voos})
        else:
            return jsonify({"status": "erro", "mensagem": "Nenhum voo encontrado no tempo limite."})

    except Exception as e:
        print(f"❌ Erro no servidor: {e}")
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"\n--- MyMiles Sniper Online ---")
    app.run(host='0.0.0.0', port=port, debug=True)