import os
import logging
import json
import time
from dotenv import load_dotenv
from services.ai_engine import AIEngine

# Configuração do Log
logging.basicConfig(
    filename='processamento.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def registrar_inicio():
    """Adiciona uma linha divisória no log para facilitar a leitura."""
    logging.info("="*50)
    logging.info("INÍCIO DE UMA NOVA SESSÃO DE TESTE")
    logging.info("="*50)

def validar_ambiente():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ ERRO: GEMINI_API_KEY não encontrada no .env!")
        return None
    return api_key

def validar_conexao(engine):
    print("Passo 1: Verificando conexão com a API...")
    if engine.test_connection():
        print("✅ Conexão validada! Chave ativa.")
        return True
    else:
        print("❌ Falha na conexão! Verifique o .env ou a internet.")
        return False

def executar_lote_testes(engine):
    textos = [
        "Voo de São Paulo para Miami pela American Airlines 50k milhas.",
        "Reserva Latam: GRU-JFK por 45000 pontos e 300 reais.",
        "Voo de São Paulo para Miami pela American Airlines 50k milhas." 
    ]

    print(f"\nPasso 2: Processando {len(textos)} itens...")
    
    for i, texto in enumerate(textos):
        print(f"\n--- Item {i+1}/{len(textos)} ---")
        print(f"Entrada: {texto}")
        
        resultado = engine.extrair_dados_voo(texto)
        
        print("Resultado:")
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
        
        if i < len(textos) - 1:
            print("⏱️ Aguardando 15s (Intervalo para cota gratuita)...")
            time.sleep(15)

def testar():
    """Orquestrador do diagnóstico."""
    # Agora registra o início sem apagar nada do passado
    registrar_inicio()
    
    print("\n=== Diagnóstico MyMiles v2.3 (Histórico Preservado) ===\n")
    
    api_key = validar_ambiente()
    if not api_key: return

    engine = AIEngine(api_key)

    if not validar_conexao(engine): return

    executar_lote_testes(engine)
    
    print("\n=== Diagnóstico Finalizado ===")

if __name__ == "__main__":
    testar()
    