from flask import Flask, render_template, request, jsonify
import json
import os
from engine import buscar_voos_completos

app = Flask(__name__)

# --- CARREGAMENTO DO BANCO DE DADOS SNIPER (JSON) ---
ARQUIVO_JSON = 'aeroportos_sniper.json'

def carregar_base_sniper():
    if not os.path.exists(ARQUIVO_JSON):
        print(f"❌ [SERVER] Erro: {ARQUIVO_JSON} não encontrado.")
        return []
    try:
        # Forçamos UTF-8 para garantir que acentos e caracteres especiais sejam lidos
        with open(ARQUIVO_JSON, 'r', encoding='utf-8') as f:
            dados = json.load(f)
            if isinstance(dados, list):
                print(f"✅ [SERVER] Base Sniper carregada: {len(dados)} aeroportos.")
                return dados
            return []
    except Exception as e:
        print(f"❌ [SERVER] Erro ao ler base JSON: {e}")
        return []

db_aeroportos = carregar_base_sniper()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/aeroportos')
def api_aeroportos():
    # .strip() remove espaços nas pontas, mantendo os internos (ex: "são paulo")
    query = request.args.get('q', '').lower().strip()
    
    if not query or len(query) < 2:
        return jsonify([])

    resultados = []
    for item in db_aeroportos:
        # A search_key contém nome em PT, EN e o código IATA
        s_key = str(item.get('search_key', '')).lower()
        
        if query in s_key:
            resultados.append({
                "code": item.get('code', ''),
                "name": item.get('name', ''),
                "search_key": s_key
            })
    
    # Ordenação: IATA exato > Nome começa com a busca > Resto
    resultados.sort(key=lambda x: (
        x['code'].lower() != query, 
        not x['name'].lower().startswith(query)
    ))

    print(f"🔍 [API] Busca: '{query}' | Resultados: {len(resultados)}")
    return jsonify(resultados[:10])

@app.route('/buscar', methods=['POST'])
def buscar():
    try:
        data = request.json
        origem = data.get('origem', '').upper().strip()
        destino = data.get('destino', '').upper().strip()
        data_ida = data.get('data_ida')
        data_volta = data.get('data_volta')
        custo_milheiro = float(data.get('custo_milheiro', 17.50))
        pax = int(data.get('pax', 1))
        classe = data.get('classe', 'ECONOMY')

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
            return jsonify({"status": "erro", "mensagem": "Nenhum voo encontrado."})
            
        return jsonify({"status": "sucesso", "dados": res})
        
    except Exception as e:
        print(f"❌ [SERVER] Erro no processamento: {e}")
        return jsonify({"status": "erro", "mensagem": str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)