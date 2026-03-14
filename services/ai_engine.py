import logging
import time
import random
import json
import os
import hashlib
from google import genai  # IMPORTANTE: Esta é a nova importação correta

class AIEngine:
    def __init__(self, api_key: str):
        # A inicialização correta para a nova biblioteca
        self.client = genai.Client(api_key=api_key)
        self.cache_file = 'cache_voos.json'
        self._carregar_cache()
        logging.info("AIEngine inicializado com a nova biblioteca google-genai.")

    def _obter_modelos_disponiveis(self):
        """Consulta a API para obter nomes de modelos válidos."""
        try:
            # Na nova API, a listagem de modelos é feita via client.models
            modelos = [m.name for m in self.client.models.list() if "flash" in m.name]
            return modelos if modelos else ["gemini-2.0-flash"]
        except Exception as e:
            logging.error(f"Erro ao listar modelos: {e}")
            return ["gemini-2.0-flash"]

    def _carregar_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
            except Exception as e:
                logging.error(f"Erro ao ler cache: {e}")
                self.cache = {}
        else:
            self.cache = {}

    def _salvar_cache(self):
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logging.error(f"Erro ao salvar cache: {e}")

    def _gerar_hash(self, texto):
        return hashlib.md5(texto.strip().lower().encode()).hexdigest()

    def test_connection(self):
        try:
            self.client.models.list()
            return True
        except Exception as e:
            logging.error(f"Erro de conexão: {e}")
            return False

    def extrair_dados_voo(self, texto_bruto: str, max_tentativas=4):
        texto_hash = self._gerar_hash(texto_bruto)
        if texto_hash in self.cache:
            logging.info("Resultado recuperado do cache local.")
            return self.cache[texto_hash]

        model_pool = self._obter_modelos_disponiveis()
        texto_limpo = " ".join(texto_bruto.split())
        prompt = (
            "Extraia voos do texto e retorne estritamente JSON: "
            "{'voos': [{'cia': '', 'milhas': 0, 'taxas': 0.0, 'trecho': ''}]}. "
            f"Texto: {texto_limpo}"
        )

        tentativa = 0
        while tentativa < max_tentativas:
            model_id = model_pool[tentativa % len(model_pool)]
            
            try:
                logging.info(f"Tentativa {tentativa + 1} usando {model_id}...")
                
                # Nova sintaxe para geração de conteúdo
                response = self.client.models.generate_content(
                    model=model_id,
                    contents=prompt,
                    config={'response_mime_type': 'application/json'}
                )
                
                resultado = json.loads(response.text)
                if resultado.get("voos") is not None:
                    self.cache[texto_hash] = resultado
                    self._salvar_cache()
                return resultado

            except Exception as e:
                tentativa += 1
                erro_str = str(e).lower()
                
                if any(err in erro_str for err in ["429", "quota", "limit", "500", "503"]):
                    espera = (tentativa * 30) + random.uniform(10, 20)
                    print(f"⚠️ Limite atingido ({model_id}). Aguardando {espera:.2f}s...")
                    time.sleep(espera)
                else:
                    logging.error(f"Erro com modelo {model_id}: {e}")
                    if "404" in erro_str:
                        continue 
                    break
                    
        return {"voos": []}
    