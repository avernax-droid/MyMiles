from flask import Flask, render_template, request, jsonify
from engine import buscar_voos_completos

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/buscar', methods=['POST'])
def buscar():
    try:
        data = request.json
        
        # Captura os dados do frontend com fallbacks seguros
        origem = data.get('origem', '').upper()
        destino = data.get('destino', '').upper()
        data_ida = data.get('data_ida')
        data_volta = data.get('data_volta')
        custo_milheiro = float(data.get('custo_milheiro', 17.50))
        pax = int(data.get('pax', 1)) # GARANTE QUE O PAX SEJA TRATADO COMO INTEIRO
        classe = data.get('classe', 'ECONOMY')

        # Chamada para o engine.py
        res = buscar_voos_completos(
            origem=origem,
            destino=destino,
            data_ida=data_ida,
            data_volta=data_volta,
            custo_milheiro=custo_milheiro,
            pax=pax,
            classe=classe
        )
        
        if not res:
            return jsonify({"status": "erro", "mensagem": "Nenhum voo encontrado ou erro na captura do token."})
            
        return jsonify({"status": "sucesso", "dados": res})
        
    except Exception as e:
        print(f"❌ [SERVER] Erro no processamento: {e}")
        return jsonify({"status": "erro", "mensagem": str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)