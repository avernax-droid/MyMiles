from flask import Flask, render_template, request, jsonify
import pandas as pd
from engine import buscar_voos_completos

app = Flask(__name__)

# --- CARREGAMENTO REFINADO DA BASE DE AEROPORTOS (OurAirports) ---
try:
    print("🚀 [SERVER] Carregando base de aeroportos...")
    df_full = pd.read_csv('airports.csv')
    
    # Filtro Sniper: Precisa ter código IATA e o aeroporto deve estar ativo (não fechado)
    df_airports = df_full.dropna(subset=['iata_code']).copy()
    df_airports = df_airports[df_airports['type'] != 'closed']
    
    # Selecionamos as colunas e limpamos valores nulos para evitar erros na busca
    df_airports = df_airports[['name', 'iata_code', 'municipality', 'iso_country']].fillna('')
    
    print(f"✅ [SERVER] Base refinada carregada: {len(df_airports)} aeroportos prontos.")
except Exception as e:
    print(f"❌ [SERVER] Erro crítico ao carregar airports.csv: {e}")
    df_airports = pd.DataFrame()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/aeroportos')
def api_aeroportos():
    query = request.args.get('q', '').lower()
    if len(query) < 2:
        return jsonify([])

    # Busca Refinada: Código IATA (início), Cidade ou Nome do Aeroporto
    mask = (
        df_airports['iata_code'].str.lower().str.startswith(query) | 
        df_airports['municipality'].str.lower().str.contains(query) |
        df_airports['name'].str.lower().str.contains(query)
    )
    
    # Pegamos os 10 melhores resultados
    resultados = df_airports[mask].head(10)
    
    lista_sugestoes = []
    for _, row in resultados.iterrows():
        # Exibe Cidade - Nome do Aeroporto (País)
        nome_exibicao = f"{row['municipality']} - {row['name']} ({row['iso_country']})"
        # Se a cidade estiver vazia no CSV, ajusta a exibição
        if not row['municipality']:
            nome_exibicao = f"{row['name']} ({row['iso_country']})"
            
        lista_sugestoes.append({
            "name": nome_exibicao,
            "code": row['iata_code']
        })
        
    return jsonify(lista_sugestoes)

@app.route('/buscar', methods=['POST'])
def buscar():
    try:
        data = request.json
        origem = data.get('origem', '').upper()
        destino = data.get('destino', '').upper()
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