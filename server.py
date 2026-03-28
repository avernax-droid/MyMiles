from flask import Flask, render_template, request, jsonify
from engine import buscar_voos_completos

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/buscar', methods=['POST'])
def buscar():
    try:
        params = request.json
        print(f"🚀 Sniper Ativado: {params['origem']} -> {params['destino']} | Pax: {params['pax']}")

        resultados = buscar_voos_completos(
            origem=params['origem'], 
            destino=params['destino'], 
            data_ida=params['data_ida'], 
            data_volta=params.get('data_volta'),
            custo_milheiro=params['custo_milheiro'],
            pax=params['pax'],
            classe=params.get('classe', 'economy')
        )
        
        if not resultados:
            return jsonify({"status": "erro", "mensagem": "Nenhum voo encontrado para este trecho ou data."})
            
        return jsonify({"status": "sucesso", "dados": resultados})

    except Exception as e:
        print(f"❌ Erro no Servidor: {e}")
        return jsonify({"status": "erro", "mensagem": "Erro interno no processamento."})

if __name__ == '__main__':
    # O host 0.0.0.0 permite que o ngrok redirecione para cá
    app.run(debug=True, host='0.0.0.0', port=5000)