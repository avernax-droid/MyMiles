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
        # Adicionamos a captura da 'classe' vinda do JSON (index.html)
        res = buscar_voos_completos(
            origem=data['origem'].upper(),
            destino=data['destino'].upper(),
            data_ida=data['data_ida'],
            data_volta=data.get('data_volta'),
            custo_milheiro=float(data['custo_milheiro']),
            pax=int(data['pax']),
            classe=data.get('classe', 'ECONOMY')  # <--- O argumento faltante aqui!
        )
        
        if not res:
            return jsonify({"status": "erro", "mensagem": "Nenhum voo encontrado."})
            
        return jsonify({"status": "sucesso", "dados": res})
        
    except Exception as e:
        # Imprime o erro no terminal para facilitar o debug se algo falhar
        print(f"❌ Erro no processamento: {e}")
        return jsonify({"status": "erro", "mensagem": str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)