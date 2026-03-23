import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

def listar_modelos():
    client = genai.Client(api_key=api_key)
    print("--- Modelos Disponíveis para sua Chave ---")
    try:
        # Lista todos os modelos que sua chave pode acessar
        for model in client.models.list():
            print(f"Nome: {model.name} | Versão: {model.version}")
    except Exception as e:
        print(f"Erro ao listar modelos: {e}")

if __name__ == "__main__":
    listar_modelos()
    