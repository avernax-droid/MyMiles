from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS 
from services.ai_engine import AIEngine
import os
import io
import csv
import json
import logging
from dotenv import load_dotenv

# Configuração de Log
logging.basicConfig(
    filename='processamento.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

load_dotenv()

app = Flask(__name__, template_folder='.', static_folder='.')
CORS(app)

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    logging.error("Chave GEMINI_API_KEY não encontrada no .env")
    motor_ia = None
else:
    motor_ia = AIEngine(API_KEY)
    logging.info("Motor de IA inicializado com sucesso.")

def calcular_auditoria(milhas, taxas):
    try:
        m = float(milhas)
        t = float(taxas)
        return round((m / 1000 * 10.0) + t, 2)
    except Exception as e:
        logging.warning(f"Erro ao calcular auditoria: {e}")
        return 0.0

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/exportar', methods=['POST'])
def exportar():
    data = request.json
    voos = data.get('voos', [])
    formato = data.get('formato', 'csv')

    if not voos:
        return jsonify({"erro": "Sem dados para exportar"}), 400

    logging.info(f"Exportando {len(voos)} voos no formato {formato}")

    if formato == 'csv':
        output = io.StringIO()
        colunas = ['cia', 'voo', 'trecho', 'milhas', 'taxas', 'custo_total_estimado']
        cabecalhos = {
            'cia': 'Cia', 'voo': 'Voo/Hora', 'trecho': 'Trecho',
            'milhas': 'Milhas', 'taxas': 'Taxas (R$)', 'custo_total_estimado': 'Total Estimado (R$)'
        }
        writer = csv.DictWriter(output, fieldnames=colunas, delimiter=';', extrasaction='ignore')
        writer.writerow(cabecalhos)
        writer.writerows(voos)
        conteudo = '\ufeff' + output.getvalue()
        return Response(
            conteudo,
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=mymiles_export.csv"}
        )
    else:
        return Response(
            json.dumps(voos, indent=4, ensure_ascii=False),
            mimetype="application/json",
            headers={"Content-disposition": "attachment; filename=mymiles_export.json"}
        )

@app.route('/auditar', methods=['POST'])
def auditar():
    entrada = request.json
    texto_copiado = entrada.get('texto', '')

    if not texto_copiado:
        return jsonify({"erro": "Texto vazio"}), 400

    logging.info(f"Iniciando auditoria. Tamanho do texto: {len(texto_copiado)} caracteres.")

    if not motor_ia:
        logging.error("Tentativa de auditoria com motor IA offline.")
        return jsonify({"erro": "Motor de IA não configurado"}), 500

    try:
        resultado = motor_ia.extrair_dados_voo(texto_copiado)
        
        if "voos" in resultado and resultado["voos"]:
            for voo in resultado['voos']:
                voo['custo_total_estimado'] = calcular_auditoria(voo.get('milhas', 0), voo.get('taxas', 0.0))
            logging.info(f"Sucesso: {len(resultado['voos'])} voos encontrados.")
        else:
            logging.warning("IA processou mas não encontrou voos no texto.")
            
        return jsonify(resultado)

    except Exception as e:
        logging.error(f"Erro crítico no processamento: {str(e)}")
        return jsonify({"erro": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)