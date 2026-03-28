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
        print(f"🚀 Sniper Ativado: {params['origem']} -> {params['destino']} ({params['pax']} pax, {params['classe']})")

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
            return jsonify({"status": "erro", "mensagem": "Nenhum voo encontrado."})
            
        return jsonify({"status": "sucesso", "dados": resultados})

    except Exception as e:
        print(f"❌ Erro: {e}")
        return jsonify({"status": "erro", "mensagem": str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)