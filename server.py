from flask import Flask, render_template, request, jsonify
import logging

# Importa a lógica da sua engine.py
try:
    from engine import buscar_voos_completos
except ImportError:
    print("⚠️ Erro: Não encontrei o arquivo engine.py na mesma pasta!")

app = Flask(__name__)

# Configuração simples de Log para ver no terminal do WSL
logging.basicConfig(level=logging.INFO)

@app.route('/')
def index():
    """Rota principal que carrega a interface HTML"""
    return render_template('index.html')

@app.route('/buscar', methods=['POST'])
def buscar():
    """
    Rota que recebe a origem e destino do index.html
    e retorna os dados processados pela engine.py
    """
    try:
        # Pega os dados JSON enviados pelo 'fetch' do JavaScript
        params = request.get_json()
        
        if not params:
            return jsonify({"status": "erro", "mensagem": "Dados não recebidos"}), 400
            
        origem = params.get('origem', '').upper().strip()
        destino = params.get('destino', '').upper().strip()
        
        print(f"\n🚀 MyMiles Sniper iniciando busca: {origem} -> {destino}")
        
        # Chama a função principal da sua engine.py
        # Ela já deve chamar o scraper.py internamente para o Token
        dados_voos = buscar_voos_completos(origem, destino)
        
        if dados_voos and len(dados_voos) > 0:
            print(f"✅ Sucesso: {len(dados_voos)} trechos encontrados.")
            return jsonify({
                "status": "sucesso",
                "dados": dados_voos
            })
        else:
            print("⚠️ Aviso: Engine retornou lista vazia.")
            return jsonify({
                "status": "erro", 
                "mensagem": "Nenhum resultado encontrado para este trecho ou erro na API."
            }), 200 # Retornamos 200 para o JS tratar o 'vazio' amigavelmente

    except Exception as e:
        print(f"❌ Erro crítico no Servidor: {e}")
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

if __name__ == '__main__':
    # host='0.0.0.0' permite que o Windows acesse o Flask dentro do WSL
    # port=5000 é o padrão. Se der erro de porta ocupada, mude para 5001
    print("\n--- SERVIDOR MYMILES ONLINE ---")
    print("Acesse no Windows: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)